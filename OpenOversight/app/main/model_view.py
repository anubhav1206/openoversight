import datetime
from typing import Callable, Union

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_sqlalchemy.model import DefaultMeta
from flask_wtf import FlaskForm as Form

from OpenOversight.app.utils.constants import HTTP_METHOD_GET, HTTP_METHOD_POST
from OpenOversight.app.utils.db import add_department_query
from OpenOversight.app.utils.forms import set_dynamic_default

from ..auth.utils import ac_or_admin_required
from ..models import db, Tag


class ModelView(MethodView):
    model = None  # type: DefaultMeta
    model_name = ""
    per_page = 20
    order_by = ""  # this should be a field on the model
    descending = False  # used for order_by
    form = ""  # type: Form
    create_function = ""  # type: Union[str, Callable]
    department_check = False

    def get(self, obj_id):
        if obj_id is None:
            if request.args.get("page"):
                page = int(request.args.get("page"))
            else:
                page = 1

            if self.order_by:
                if not self.descending:
                    objects = self.model.query.order_by(
                        getattr(self.model, self.order_by)
                    ).paginate(page=page, per_page=self.per_page, error_out=False)
                objects = self.model.query.order_by(
                    getattr(self.model, self.order_by).desc()
                ).paginate(page=page, per_page=self.per_page, error_out=False)
            else:
                objects = self.model.query.paginate(
                    page=page, per_page=self.per_page, error_out=False
                )

            return render_template(
                "{}_list.html".format(self.model_name),
                objects=objects,
                url="main.{}_api".format(self.model_name),
            )
        else:
            obj = self.model.query.get_or_404(obj_id)
            return render_template(
                "{}_detail.html".format(self.model_name),
                obj=obj,
                current_user=current_user,
            )

    @login_required
    @ac_or_admin_required
    def new(self, form=None):
        if not form:
            form = self.get_new_form()
            if hasattr(form, "department"):
                add_department_query(form, current_user)
                if getattr(current_user, "dept_pref_rel", None):
                    set_dynamic_default(form.department, current_user.dept_pref_rel)
            if hasattr(form, "creator_id") and not form.creator_id.data:
                form.creator_id.data = current_user.get_id()
            if hasattr(form, "last_updated_id"):
                form.last_updated_id.data = current_user.get_id()

        if form.validate_on_submit():
            new_obj = self.create_function(form)
            db.session.add(new_obj)
            db.session.commit()
            # OOVA-tags
            if (type(new_obj).__name__ == "Incident"):
                new_tags = request.form.getlist("tags[]")
                tags = []
                for new_tag in new_tags:
                    if (new_tag.isdigit()):
                        tag = Tag.query.filter_by(id=new_tag).first()
                        if tag is not None:
                            tags.append(tag)
                    else:
                        tag = db.session.add(Tag(
                                    tag=new_tag
                                ))
                        db.session.commit()
                        tag = Tag.query.filter_by(tag=new_tag).first()
                        tags.append(tag)

                new_obj.tags = tags
                db.session.commit()
            flash("{} created!".format(self.model_name))
            return self.get_redirect_url(obj_id=new_obj.id)
        else:
            current_app.logger.info(form.errors)

        return render_template("{}_new.html".format(self.model_name), form=form)

    @login_required
    @ac_or_admin_required
    def edit(self, obj_id, form=None):
        obj = self.model.query.get_or_404(obj_id)
        if self.department_check:
            if (
                not current_user.is_administrator
                and current_user.ac_department_id != self.get_department_id(obj)
            ):
                abort(403)

        if not form:
            form = self.get_edit_form(obj)
            # if the object doesn't have a creator id set, st it to current user
            if (
                hasattr(obj, "creator_id")
                and hasattr(form, "creator_id")
                and getattr(obj, "creator_id")
            ):
                form.creator_id.data = obj.creator_id
            elif hasattr(form, "creator_id"):
                form.creator_id.data = current_user.get_id()

            # if the object keeps track of who updated it last, set to current user
            if hasattr(form, "last_updated_id"):
                form.last_updated_id.data = current_user.get_id()

        if hasattr(form, "department"):
            add_department_query(form, current_user)

        if form.validate_on_submit():
            self.populate_obj(form, obj)
            flash("{} successfully updated!".format(self.model_name))
            return self.get_redirect_url(obj_id=obj_id)

        return render_template(
            "{}_edit.html".format(self.model_name), obj=obj, form=form
        )

    @login_required
    @ac_or_admin_required
    def delete(self, obj_id):
        obj = self.model.query.get_or_404(obj_id)
        if self.department_check:
            if (
                not current_user.is_administrator
                and current_user.ac_department_id != self.get_department_id(obj)
            ):
                abort(403)

        if request.method == HTTP_METHOD_POST:
            db.session.delete(obj)
            db.session.commit()
            flash("{} successfully deleted!".format(self.model_name))
            return self.get_post_delete_url()

        return render_template("{}_delete.html".format(self.model_name), obj=obj)

    def get_edit_form(self, obj):
        form = self.form(obj=obj)
        return form

    def get_new_form(self):
        return self.form()

    def get_redirect_url(self, *args, **kwargs):
        # returns user to the show view
        return redirect(
            url_for(
                "main.{}_api".format(self.model_name),
                obj_id=kwargs["obj_id"],
                _method=HTTP_METHOD_GET,
            )
        )

    def get_post_delete_url(self, *args, **kwargs):
        # returns user to the list view
        return redirect(url_for("main.{}_api".format(self.model_name)))

    def get_department_id(self, obj):
        return obj.department_id

    def populate_obj(self, form, obj):
        form.populate_obj(obj)
        if hasattr(obj, "date_updated"):
            obj.date_updated = datetime.datetime.now()
        db.session.add(obj)
        db.session.commit()

    def create_obj(self, form):
        self.model(**form.data)

    def dispatch_request(self, *args, **kwargs):
        # isolate the method at the end of the url
        end_of_url = request.url.split("/")[-1].split("?")[0]
        endings = ["edit", "new", "delete"]
        meth = None
        for ending in endings:
            if end_of_url == ending:
                meth = getattr(self, ending, None)
        if not meth:
            if request.method == HTTP_METHOD_GET:
                meth = getattr(self, "get", None)
            else:
                assert meth is not None, "Unimplemented method %r" % request.method
        return meth(*args, **kwargs)

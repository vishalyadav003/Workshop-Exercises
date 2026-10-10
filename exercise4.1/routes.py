"""Routes, filtering, and server-side validation for the notice board."""
import secrets
from datetime import date

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for

import models

bp = Blueprint("notices", __name__)
FIELDS = ("kind", "category", "description", "zone", "event_date", "contact")


def _token():
    token = session.get("form_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["form_token"] = token
    return token


def _valid_token():
    supplied = request.form.get("csrf_token", "")
    expected = session.get("form_token", "")
    if not supplied or not expected or not secrets.compare_digest(supplied, expected):
        return False
    # Consume the token: replays and duplicate POSTs cannot create another notice.
    session.pop("form_token", None)
    return True


def _values():
    values = {name: request.form.get(name, "").strip() for name in FIELDS}
    errors = []
    if values["kind"] not in models.KINDS:
        errors.append("Choose Lost or Found.")
    if values["category"] not in models.CATEGORIES:
        errors.append("Choose an allowed item category.")
    if values["zone"] not in models.ZONES:
        errors.append("Choose a location zone.")
    if not values["description"]:
        errors.append("Description is required.")
    elif len(values["description"]) > models.MAX_DESCRIPTION:
        errors.append(f"Description must be {models.MAX_DESCRIPTION} characters or fewer.")
    if not values["event_date"]:
        errors.append("Date found/lost is required.")
    else:
        try:
            parsed = date.fromisoformat(values["event_date"])
            if parsed > date.today():
                errors.append("Date found/lost cannot be in the future.")
        except ValueError:
            errors.append("Enter a valid date.")
    if not values["contact"]:
        errors.append("Contact preference is required.")
    elif len(values["contact"]) > 120:
        errors.append("Contact preference must be 120 characters or fewer.")
    return values, errors


@bp.get("/")
def index():
    query = request.args.get("q", "").strip().casefold()
    category = request.args.get("category", "")
    zone = request.args.get("zone", "")
    notices = [n for n in models.all_notices() if not n.get("resolved")]
    if category in models.CATEGORIES:
        notices = [n for n in notices if n["category"] == category]
    if zone in models.ZONES:
        notices = [n for n in notices if n["zone"] == zone]
    if query:
        notices = [n for n in notices if query in " ".join((n["description"], n["category"], n["zone"], n["kind"])).casefold()]
    return render_template("index.html", notices=notices, categories=models.CATEGORIES, zones=models.ZONES,
                           filters={"q": request.args.get("q", ""), "category": category, "zone": zone})


@bp.get("/notice/<notice_id>")
def detail(notice_id):
    notice = models.get_notice(notice_id)
    if notice is None:
        abort(404)
    return render_template("detail.html", notice=notice, csrf_token=_token())


@bp.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "GET":
        return render_template("create.html", categories=models.CATEGORIES, zones=models.ZONES,
                               kinds=models.KINDS, errors=[], values={}, csrf_token=_token(), today=date.today().isoformat())
    if not _valid_token():
        flash("This form was already submitted or expired. Review your notice and submit a fresh form.", "error")
        return redirect(url_for("notices.create"), code=303)
    values, errors = _values()
    if errors:
        return render_template("create.html", categories=models.CATEGORIES, zones=models.ZONES,
                               kinds=models.KINDS, errors=errors, values=values, csrf_token=_token(),
                               today=date.today().isoformat()), 400
    record = models.create_notice(values)
    flash("Your notice has been posted.", "success")
    return redirect(url_for("notices.detail", notice_id=record["id"]), code=303)


@bp.post("/notice/<notice_id>/resolve")
def resolve(notice_id):
    if not _valid_token():
        flash("This action was already submitted or expired.", "error")
        return redirect(url_for("notices.index"), code=303)
    record = models.resolve_notice(notice_id)
    if record is None:
        abort(404)
    flash("Notice marked as resolved.", "success")
    return redirect(url_for("notices.detail", notice_id=notice_id), code=303)

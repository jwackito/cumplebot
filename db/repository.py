from sqlalchemy import func

from .models import BotUser, Person, Subscription, UserPreference


UNSET = object()


def add_person(session, name, birthday, registered_by, message=None, is_private=False):
    person = Person(
        name=name,
        birthday=birthday,
        custom_message=message,
        is_private=is_private,
        registered_by_tg_id=registered_by,
    )
    session.add(person)
    session.commit()
    return person


def update_person(session, person, name=None, birthday=None, custom_message=_UNSET):
    if name is not None:
        person.name = name
    if birthday is not None:
        person.birthday = birthday
    if custom_message is not UNSET:
        person.custom_message = custom_message
    session.commit()
    return person


def remove_person(session, name):
    person = session.query(Person).filter_by(name=name).first()
    if person:
        session.delete(person)
        session.commit()
    return person


def get_person(session, name):
    return session.query(Person).filter_by(name=name).first()


def get_person_by_id(session, person_id):
    return session.get(Person, person_id)


def get_all_persons(session):
    return session.query(Person).order_by(Person.name).all()


def get_public_persons(session):
    return (
        session.query(Person)
        .filter(Person.is_private == False)
        .order_by(Person.name)
        .all()
    )


def add_subscription(session, subscriber_tg_id, person_id):
    sub = Subscription(subscriber_tg_id=subscriber_tg_id, person_id=person_id)
    session.add(sub)
    session.commit()
    return sub


def remove_subscription(session, subscriber_tg_id, person_id):
    sub = (
        session.query(Subscription)
        .filter_by(subscriber_tg_id=subscriber_tg_id, person_id=person_id)
        .first()
    )
    if sub:
        session.delete(sub)
        session.commit()
    return sub


def get_subscription(session, subscriber_tg_id, person_id):
    return (
        session.query(Subscription)
        .filter_by(subscriber_tg_id=subscriber_tg_id, person_id=person_id)
        .first()
    )


def get_subscriptions_for_user(session, subscriber_tg_id):
    return (
        session.query(Subscription)
        .join(Person)
        .filter(Subscription.subscriber_tg_id == subscriber_tg_id)
        .order_by(Person.name)
        .all()
    )


def get_or_create_user_preference(session, tg_id):
    pref = session.get(UserPreference, tg_id)
    if not pref:
        pref = UserPreference(tg_id=tg_id, notification_time="09:00")
        session.add(pref)
        session.commit()
    return pref


def set_notification_time(session, tg_id, time_str):
    pref = get_or_create_user_preference(session, tg_id)
    pref.notification_time = time_str
    session.commit()
    return pref


def ensure_user(session, tg_id):
    user = session.get(BotUser, tg_id)
    if not user:
        user = BotUser(tg_id=tg_id)
        session.add(user)
        session.commit()
    return user


def get_all_users(session):
    return session.query(BotUser).all()


def auto_subscribe_all(session, person_id, exclude_tg_id=None):
    users = get_all_users(session)
    for user in users:
        if exclude_tg_id is not None and user.tg_id == exclude_tg_id:
            continue
        existing = get_subscription(session, user.tg_id, person_id)
        if not existing:
            add_subscription(session, user.tg_id, person_id)


def get_due_subscriptions(session, current_hhmm, today):
    month_day = today.strftime("%m-%d")
    return (
        session.query(Subscription)
        .join(Person)
        .outerjoin(UserPreference, UserPreference.tg_id == Subscription.subscriber_tg_id)
        .filter(
            func.coalesce(UserPreference.notification_time, "09:00") == current_hhmm,
            func.strftime("%m-%d", Person.birthday) == month_day,
            (Subscription.last_notified_date != today)
            | (Subscription.last_notified_date.is_(None)),
        )
        .all()
    )

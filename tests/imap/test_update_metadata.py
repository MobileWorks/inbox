from inbox.crispin import GmailFlags
from inbox.models import Thread, Folder
from inbox.models.backends.imap import ImapUid
from inbox.mailsync.backends.imap.common import update_metadata
from tests.util.base import add_fake_message

ACCOUNT_ID = 1
NAMESPACE_ID = 1


def test_update_metadata(db):
    """Check that threads are updated correctly when a label that we haven't
    seen before is added to multiple threads -- previously, this would with an
    IntegrityError because autoflush was disabled."""
    first_thread = db.session.query(Thread).get(1)
    second_thread = db.session.query(Thread).get(2)
    folder = db.session.query(Folder).filter(
        Folder.account_id == ACCOUNT_ID,
        Folder.name == '[Gmail]/All Mail').one()
    uids = []

    first_thread_uids = (22222, 22223)
    for msg_uid in first_thread_uids:
        message = add_fake_message(db.session, NAMESPACE_ID, first_thread)
        uids.append(ImapUid(account_id=ACCOUNT_ID, message=message,
                            msg_uid=msg_uid, folder=folder))

    second_thread_uids = (22224, 22226)
    for msg_uid in second_thread_uids:
        message = add_fake_message(db.session, NAMESPACE_ID, second_thread)
        uids.append(ImapUid(account_id=ACCOUNT_ID, message=message,
                            msg_uid=msg_uid, folder=folder))
    db.session.add_all(uids)
    db.session.commit()

    msg_uids = first_thread_uids + second_thread_uids

    new_flags = {msg_uid: GmailFlags((), (u'\\some_new_label',))
                 for msg_uid in msg_uids}
    update_metadata(ACCOUNT_ID, db.session, folder.name, folder.id, msg_uids,
                    new_flags)
    db.session.commit()
    assert 'some_new_label' in [tag.name for tag in first_thread.tags]
    assert 'some_new_label' in [tag.name for tag in second_thread.tags]

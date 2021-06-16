
def send_token_mail(box, f, t, s, p):
    import subprocess

    return subprocess.run(["python", "do_the_mail_thing.py", str(box), str(f), str(t), str(s), str(p)]).returncode == 0 #, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def send_token_mail_real(box, f, t, s, p):
    import mailbox

    try:
        mb = mailbox.Maildir("~/users/{}".format(box), create=False)
    except mailbox.NoSuchMailboxError as e:
        print(e)
        return False

    mb.lock()

    try:
        msg = mailbox.MaildirMessage()
        #msg.set_subdir('new')
        #msg.set_date(time.time())
        msg.add_flag('F')   # mark as important
        msg['From'] = f
        msg['To'] = t
        msg['Subject'] = s
        msg.set_payload(p)

        mb.add(msg)
        mb.flush()

        return True
    except Exception as e:
        print(e)
        return False
    finally:
        mb.unlock()


def send_genuine_mail(f: str, t: list, s: str, p: str, tmp_pass=None):
    import smtplib, os
    from email.message import Message

    msg = Message()
    msg['From'] = f
    msg['To'] = t
    msg['Subject'] = s
    msg.set_payload(p)

    with smtplib.SMTP(host='localhost', port=587) as smtp:
        #smtp.set_debuglevel(1)
        smtp.starttls()
        smtp.login(f, tmp_pass)
        smtp.sendmail(f, t, str(msg))
        smtp.quit()


if __name__ == "__main__":
    import sys
    send_token_mail_real(*sys.argv[1:])

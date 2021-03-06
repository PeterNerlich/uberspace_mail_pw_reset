
def send_token_mail(box, f, t, s, p):
    import subprocess

    return subprocess.run(["python", "do_the_mail_thing.py", str(box), str(f), str(t), str(s), str(p)]).returncode == 0 #, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def send_token_mail_real(box, f, t, s, p):
    from email.message import EmailMessage
    import mailbox

    msg = EmailMessage()
    msg['From'] = f
    msg['To'] = t
    msg['Subject'] = s
    msg.set_content(p)

    try:
        mb = mailbox.Maildir("~/users/{}".format(box), create=False)
    except mailbox.NoSuchMailboxError as e:
        print(e)
        return False

    mb.lock()

    try:
        msg = mailbox.MaildirMessage(msg)
        #msg.set_subdir('new')
        #msg.set_date(time.time())
        msg.add_flag('F')   # mark as important

        mb.add(msg)
        mb.flush()

        return True
    except Exception as e:
        print(e)
        return False
    finally:
        mb.unlock()


def send_genuine_mail(f, t, s, p, tmp_pass=None, genuine=None):
    import subprocess

    return subprocess.run(["python", "do_the_mail_thing.py", str(f), str(t), str(s), str(p), str(tmp_pass), str(1)]).returncode == 0 #, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def send_genuine_mail_real(f: str, t: str, s: str, p: str, tmp_pass=None, genuine=None):
    import smtplib, os
    from email.message import EmailMessage

    msg = EmailMessage()
    msg['From'] = f
    msg['To'] = t
    msg['Subject'] = s
    msg.set_content(p)

    with smtplib.SMTP(host='localhost', port=587) as smtp:
        smtp.starttls()
        smtp.login(f, tmp_pass)
        smtp.sendmail(f, t.split(','), str(msg))
        smtp.quit()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 6:
        send_genuine_mail_real(*sys.argv[1:])
    else:
        send_token_mail_real(*sys.argv[1:])

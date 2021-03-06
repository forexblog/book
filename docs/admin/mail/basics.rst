.. _admin.basics:

========================
Mail server basics
========================

.. glossary::

  mail server

    A server that runs an MTA (mail transfer agent) like postfix and is set up
    accordingly.

  relay host

    A mail server that accepts outgoing mails from other :term:`mail servers
    <mail server>` and cares about delivering them to their final destination.


Using a relay host
==================

Using a :term:`relay host` means to delegate all outgoing mail to a single
third-party mail server that is specialized in talking to the mail servers of
the recipients.

This can make sense because talking with SMTP servers is a complex topic. For
example you need to make them trust that you are not a spammer. It's
understandable that these servers are very paranoid regarding spammers.

A :term:`relay host` can be any third-party smtpd server as provided by Mailgun,
SendGrid, AWS, Rackspace, Google, or your own server in another data center.
Some ISPs offer a free relay host for the virtual machines they provide.
`Mailgun <https://www.mailgun.com/smtp/free-smtp-service/free-open-smtp-relay/>`__
gives you 10000 free emails every month.

When you configure the MTA on your :term:`mail server` to use a :term:`relay
host`, you can skip the remaining things described on this page.


Without a relay host
====================

When you don't want to buy relay hosting service from a third party, you must
learn how to do it yourself.

To run your :term:`mail server` without a relay host, you need a static IP
address and a fully qualified domain name pointing to it. There can be only one
mail server per IP address. You must care about `Reverse DNS`_, `SPF`_, `DMARC`_
and `DKIM`_.

Some examples of sender guidelines:

- https://www.gmx.net/mail/senderguidelines/
- https://support.google.com/mail/answer/81126
- https://sendersupport.olc.protection.outlook.com/pm/policies.aspx


Reverse DNS
===========

For an independent mail server you must make that the Reverse DNS of your IP
address is configured correctly.

While DNS maps a domain name to an IP address, reverse DNS maps an IP address to
a domain name.  It is a way of publicly declaring that your server at that IP
address is responding to your domain name. The provider of your server is the
owner of the IP address and they usually have a means for you to tell them the
Reverse DNS.

Without a reverse DNS the SMTP servers of your recipients are likely to refuse
to talk with your server.

Reverse DNS (also known as PTR record) means that the owner of an IP address
declares publicly the FQDN that points to this address.

You can use :cmd:`dig` to do a DNS lookup, and  :cmd:`dig -x` to do a reverse
DNS lookup. :cmd:`dig laudate.ee` gives me `95.217.218.29` and :cmd:`dig -x
95.217.218.29` gives me `mail.laudate.ee`.

Why ``mail.laudate.ee`` instead of simply ``laudate.ee``? Both FQDN resolve to
the same IP address when we configured a wildcard in the zone file. It seems
that the `mail` subdomain (or sometimes `smtp` or `mx`) is general practice.  It
makes sense to have your mail server on a different machine than your
application.  Already for security reasons. Also in order to be scalable.

Note : the domain given by the MX record (the FQDN of our mail server) needs to
have its separate A record. Just a CNAME is not enough for a mail server.

.. _SPF:

SPF
===

The Sender policy framework (SPF) is defined by `RFC 7208
<http://www.faqs.org/rfcs/rfc7208.html>`__) as an authentication process that
ties the `envelope from` field (defined by `RFC 5321
<http://www.faqs.org/rfcs/rfc5321.html>`__) to a set of authorized sender IP
addresses.  This authorization is published in a TXT record in DNS. Receivers
can check SPF at the beginning of a SMTP transaction, compare the connecting IP
address  to the IP specified by the `envelope from` field domain and thus
validate whether that IP is authorized to send mail.

The SPF TXT record contains (1) a version indicator, (2) a list of allowed IPs
and (3) an authorization type.

- version indicator is always the same string ``v=spf1``

- IPs can be
  - keyword "mx" means ""
  - either IPv4 space or IPv6 space

Authorization type can be one of the following:

==== ========= ===============================
+all pass      Allow all mail
-all fail      Only allow mail that matches one of the parameters (IPv4, MX, etc) in the record
~all softfail  Allow mail whether or not it matches the parameters in the record
?all neutral   No policy statement
==== ========= ===============================

.. _DMARC:

DMARC
=====

DMARC (Domain-based Message Authentication, Reporting and Conformance) is a way
for the receiving mail server to give feedback to the sending mail server about
what happened to their message.  A message can "pass", go into "quarantine" or
get "rejected". DMARC builds upon both the DKIM and Sender Policy Framework
(SPF) specifications that are currently being developed within the IETF.

A DMARC resource record in the DNS looks like this::

  "v=DMARC1;p=reject;pct=100;rua=mailto:postmaster@mydomain.org"

In this example the sending mail server asks the receiver to boldly **reject**
all non-aligned messages and send an **aggregate** report about the rejections
to <postmaster@mydomain.org>.

DMARC records use the same "tag-value" syntax for DNS-based key records defined
in DKIM.

.. _DKIM:

DKIM (DomainKeys Identified Mail)
=================================

DKIM is an authentication mechanism for email that uses a "domain name
identifier" and a DNS-based publishing service for the public key. We use it to
avoid email spoofing and  because otherwise our server would be suspected to
send spam, which would cause delivery issues.

When using DKIM, Postfix is configured to sign every outgoing message content.
The signature information is placed into a field of the message header. The
receiving mail server can then validate the signature to check that our server
took responsibility for the message.

Here is an installation cheat sheet for using it with postfix.  Replace
``mydomain.org`` with your domain. The examples use ``mail`` as the selector.
Selectors are used when you have more than one key per domain, e.g. one for
"advertisement" and another for "invoicing". Common alternative values for the
default selector are ``dkim`` or simply ``default``.

Install the system package::

  $ sudo apt-get install opendkim opendkim-tools

Edit your :xfile:`/etc/opendkim.conf` and set the following values::

  Domain    mydomain.org
  KeyFile   /etc/postfix/dkim.key
  Selector  mail
  Socket    inet:8891@localhost

Edit your :xfile:`/etc/default/opendkim` and set the following values::

  RUNDIR=/var/run/opendkim
  SOCKET=inet:8891@localhost

Edit your :xfile:`/etc/postfix/main.cf` and set the following values::

  milter_default_action = accept
  milter_protocol = 2
  smtpd_milters = inet:8891@localhost
  non_smtpd_milters = inet:8891@localhost

Generate your DKIM key::

  $ opendkim-genkey -t -s mail -d mydomain.org

This will create two files :xfile:`mail.private` and :xfile:`mail.txt`.
The former is our private key that we will used to sign outgoing emails.
Move it to the location we specified earlier in :xfile:`/etc/opendkim.conf`::

  $ sudo mv mail.private mail.txt /etc/postfix/
  $ cd /etc/postfix/
  $ sudo ln -s mail.private dkim.key

Paste the public key into a TXT record of your DNS zone file::

  $ cat mail.txt

  v=DKIM1; h=sha256; k=rsa; t=y; p=T1Wxyz...very long string...AQAB

It might take some time for changes to propagate.  Restart the services::

  $ sudo service opendkim start
  $ sudo service postfix restart


Check whether propagation is done::

  $ dig mail._domainkey.mydomain.org txt

This should return something like::

  ;; ANSWER SECTION:
  mail._domainkey.saffre-rumma.net. 3600 IN CNAME	mydomain.org.
  mydomain.org.	3600	IN	TXT	"v=spf1 ip4:167.114.252.122  -all"
  mydomain.org.	3600	IN	TXT	"v=DKIM1; h=sha256; k=rsa; t=y;    p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApfLOzbgeQgyTvEe8xSBCzB8+Uj+Y9uy3/Ivf1aV3A78pDxW2XbjXV5bKmyLH8NncOfbm/T1W6Xs/8b6MidvH2u1wGvOVL8zU/Ghatr8OvAHr1Bn45KkEcAFNeUhOew2i9EVoRuHAc5Lqo0i0e1oL1WTz+I3rh1yXEIfP0Tr5jA" "ryEbiQExzXsEKh+SpV2gWFsUKlZY+gEycTjB   CvYrzukoFWUc5u5xmM2I6ndQoAUAUXgv3tuXw36Fql2eVidFUIJNUKXWF+AuK/NmZmGNTxOLIADi9zX7HuYAsVRfr4b+qSknBF54dfvBhV6gEN1t2DFxKBL5UHZXCbQXBikBmISwIDAQAB"
  mydomain.org.	3600	IN	TXT	"v=DMARC1; p=reject; ruf=mailto:postmaster@mydomain.org"


Or you can use :cmd:`opendkim-testkey`::

  $ sudo opendkim-testkey -d mydomain.org -s mail -vvv
  opendkim-testkey: using default configfile /etc/opendkim.conf
  opendkim-testkey: key loaded from /etc/postfix/dkim.key
  opendkim-testkey: checking key 'mail._domainkey.mydomain.org'
  opendkim-testkey: multiple DNS replies for 'mydomain.org'

Testing your configuration
==========================


You can try to send an email to <autorespond+dkim@dk.elandsys.com> and confirm
it's being signed.

You can also use http://www.protodave.com/tools/dkim-key-checker/

or https://tools.sparkpost.com/dkim

One good method to test is using swaks::

  swaks -t check-auth2@verifier.port25.com -f user@mydomain.org --server localhost

This will send a test email, and then get a reply with dkim and dmark information.
If you don't have a pop3 or imap server configured you can add this line in your your /etc/aliases to have postfix
forward mail to another server for this name.::

  sudo echo "user: myaddress@otherserver.net" >> /etc/aliases
  # Also update the alias map and restart postfix
  sudo newaliases; sudo service postfix restart

Or, as explained on `abuseat.org <https://www.abuseat.org/helocheck.html>`__::

  $ mail -s "test" helocheck@abuseat.org < /dev/null


Diagnostic tips and tricks
==========================

.. rubric:: How to send a simple mail for testing the mail system?

If `mailutils` is installed::

  $ mail -s "some test" root

If the mail comes through, watch for the ``From:`` header of it.  The
:cmd:`mail` command uses username@hostname when submitting it to the MTA. The
MTA then replaces the local hostname by your mail server's FQDN.

The GNU mail program has its own configuration files::

  $ mail --show-config-options | grep SYSCONFDIR
  SYSCONFDIR=/etc 	- System configuration directory

Which means that actually the config files are in :file:`/etc/mail`. And one of
them, :file:`/etc/mail/local-host-names` contains my default ``From`` header.

.. rubric:: Which ports is my server listening on? And which service responds to
    which port?

Say :cmd:`nmap localhost` to see this.


Troubleshooting
===============

Some problems we had when running our own mail server and how we fixed them


8891@localhost: garbage after numerical service
-----------------------------------------------

This was an odd error. On one server the inet socket connection worked fine, on the other server this error was logged by smtpd every time it sent.
I wasn't able to find the source for this issue. But the solution to use a file based socket.
However the default settings for file socket connection gives file not find errors.

The correct settings for postfix and opendkim for a file socket connection:::

    #/etc/opendkim.conf
    umask           002
    Socket			local:/var/spool/postfix/var/spool/opendkim/opendkim.sock
    #/etc/default/opendkim
    Socket=local:/var/spool/postfix/var/spool/opendkim/opendkim.sock
    #/etc/postfix/main.cf
    smtpd_milters = local:/var/spool/opendkim/opendkim.sock

The reason for /var/spool/postfix for opendkim is that postfix things that is / when looking for the file.
For this solution you also need to create that path and do some permission work.::

    sudo mkdir -p /var/spool/postfix/var/spool/opendkim/
    sudo chown opendkim:opendkim /var/spool/postfix/var/spool/opendkim/
    sudo adduser postfix opendkim

That will allow postfix to use the socket file.


You will see messages like the following in your :file:`/var/log/mail.log`
file::

  Oct 16 07:06:16 host mx01.emig.gmx.net[212.227.17.5] refused to talk to me:
  554-gmx.net (mxgmx116) Nemesis ESMTP Service not available
  554-No SMTP service 554-Bad DNS PTR resource record.
  554 For explanation visit http://postmaster.gmx.com/en/error-messages?ip=167.114.229.225&c=rdns

:message:`554 Bad DNS PTR resource record` means that your reverse DNS record
isn't set up correctly.

:message:`550 Email blocked` means that the recipient's mail server refuses to
receive your mail because your :term:`mail server` is blacklisted. To see
whether your server is blacklisted, you can ask `multirbl.valli.org
<http://multirbl.valli.org/lookup/>`__. For some nice examples of why
blacklisting is needed, see  `bobcares.com
<https://bobcares.com/blog/550-email-blocked/>`__.


:message:`550-Requested action not taken: mailbox unavailable 550 Sender address
has null MX (in reply to MAIL FROM command))` indicates that the `From:` address
of your mail was invalid.

::

  relay=gmail-smtp-in.l.google.com[2a00:1450:4010:c06::1a]:25,
  status=bounced (host gmail-smtp-in.l.google.com[2a00:1450:4010:c06::1a] said:
    550-5.7.26 Unauthenticated email from laudate.ee is not accepted due to
    domain's 550-5.7.26 DMARC policy. Please contact the administrator of
    laudate.ee domain 550-5.7.26 if this was a legitimate mail.
    Please visit 550-5.7.26  https://support.google.com/mail/answer/2451690
    to learn about the 550 5.7.26 DMARC initiative.


lost connection with mail.example.com
-------------------------------------

Another problem encountered was this::

  postfix/smtp[13506]:B08AC130BC: to=<rec@example.com>,
  relay=mail.example.com[46.4.136.153]:25, delay=134801,
  delays=134798/0.11/1.4/0.9, dsn=4.4.2,
  status=deferred (lost connection with mail.example.com[46.4.136.153] while sending MAIL FROM)

We tried open an manual connection to the server::

  $ openssl s_client -connect mail.example.com:25 -starttls smtp

Sources
=======

- https://dmarc.org/overview/
- https://easyengine.io/tutorials/mail/dkim-postfix-ubuntu/
- http://www.dkim.org/info/dkim-faq.html
- https://serverfault.com/questions/711600/reverse-dns-is-not-a-valid-hostname-error-from-mxtoolbox
- https://www.pbrumby.com/2018/05/09/dns-records-explained/
- https://mxtoolbox.com/dmarc/dkim/setup/how-to-setup-dkim
- https://www.heinlein-support.de/blog/mailserver/gmx-blockt-e-mail-adressen-ohne-aaaaa-record/
- https://stackoverflow.com/questions/4367358/whats-the-difference-between-sender-from-and-return-path
- https://wordtothewise.com/2014/06/authenticating-spf/
- http://www.postfix.org/BASIC_CONFIGURATION_README.html#relayhost
- https://www.linuxbabe.com/mail-server/setting-up-dkim-and-spf

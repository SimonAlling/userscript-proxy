# Userscript Proxy

Browser extensions on iOS, Android and pretty much any other web browsing device. No jailbreak/root required.

Userscript Proxy is built around [mitmproxy](mitmproxy) and acts as a MITM, injecting matching userscripts into web pages as they flow through it. Both HTTP and HTTPS are supported.


## Security

**UP can (and must be able to) read all HTTP(S) traffic** sent to and from the device in question, so the only reasonably secure way to use it is to run it on a server controlled by oneself.

Exceptions can be specified by adding ignore rules to `ignore.txt`. (This is even necessary for apps like Facebook Messenger and App Store, which refuse to connect through a MITM proxy.) **Traffic from/to hosts matched by such rules is not decrypted and cannot be read by mitmproxy or Userscript Proxy.**


## Data usage

UP has negligible data usage impact when no userscript is injected, i.e. for URLs without any matching userscript. However, userscripts are injected into _every_ response from a matching URL, and the size of a userscript can be anything from a few hundred bytes for the most basic ones to hundreds of kilobytes in extreme cases.

Many useful userscripts are relatively large, depending on everything from the functionality of the script to frameworks and compilation options. It is probably a good idea to have a general awareness of this issue, and to take appropriate action such as [minifying](minification) userscripts and adding suitable ignore rules.


## Functionality

UP supports (a subset of) the [Greasemonkey metadata syntax](metadata). No adaptation of userscripts should be required. These directives are supported:

  * `@name`
  * `@version`
  * `@run-at document_(start|end|idle)`
  * `@match`
  * `@include` (basic pattern and regex)
  * `@exclude`
  * `@noframes`


[mitmproxy]: https://mitmproxy.org
[minification]: https://en.wikipedia.org/wiki/Minification_(programming)
[metadata]: https://wiki.greasespot.net/Metadata_Block

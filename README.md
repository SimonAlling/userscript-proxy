# Userscript Proxy

Browser extensions on iOS, Android and pretty much any other web browsing device. No jailbreak/root required.

Userscript Proxy is built around [mitmproxy](mitmproxy) and acts as a MITM, injecting matching userscripts into web pages as they flow through it. Both HTTP and HTTPS are supported.


## Security

**UP can (and must be able to) read and modify all HTTP(S) traffic** sent to and from the device in question, so the only reasonably secure way to use it is to run it on a server controlled by oneself.

Exceptions can be specified by adding ignore rules to `ignore.txt`. (This is even necessary for apps like Facebook Messenger and App Store, which refuse to connect through a MITM proxy.) **Traffic to and from hosts matched by such rules _cannot_ be read or modified by mitmproxy or Userscript Proxy.**


## Data usage

UP has no data usage impact when no userscript is injected, i.e. for URLs without any matching userscript.
When a script _is_ injected, exactly one of the following things happens:

  * The entire userscript is injected as inline JavaScript (potentially dozens or even hundreds of kilobytes).
  * A `<script>` tag referencing the userscript is injected (~100 bytes, depending on the length of the `@downloadURL`).

A userscript is injected by reference if and only if it has a specified `@downloadURL` in its metadata.
(This can be overridden using the `--inline` flag, in which case all userscripts are injected inline.)

Userscripts are injected into _every_ response from a matching URL, and the size of a userscript can be anything from a few hundred bytes for the most basic ones to hundreds of kilobytes in extreme cases, so there are _massive_ data usage reductions to be gained from making the userscript accessible by URL and including a `@downloadURL`.
If the `@downloadURL` approach is not possible, for one reason or the other, it is a good idea to be aware of this issue, and to take appropriate action such as [minifying](minification) userscripts and adding suitable ignore rules.


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

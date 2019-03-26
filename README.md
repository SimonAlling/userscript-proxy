# Userscript Proxy

Browser extensions on iOS, Android and pretty much any other web browsing device. No jailbreak/root required.

Userscript Proxy is built around [mitmproxy](mitmproxy) and acts as a MITM, injecting matching userscripts into web pages as they flow through it. Both HTTP and HTTPS are supported.


## Security

**UP can (and must be able to) read and modify all HTTP(S) traffic** sent to and from the device in question, so the only reasonably secure way to use it is to run it on a server controlled by oneself.

Exceptions can be specified by adding ignore rules to `ignore.txt`. (This is even necessary for apps like Facebook Messenger and App Store, which refuse to connect through a MITM proxy.) **Traffic to and from hosts matched by such rules _cannot_ be read or modified by mitmproxy or Userscript Proxy.**


## Data usage

UP has no data usage impact when no userscript is injected, i.e. for URLs without any matching userscript.
When a script _is_ injected, **exactly one** of the following things happens:

  * The entire userscript is injected as inline JavaScript (potentially dozens or even hundreds of kilobytes).
  * A `<script>` tag referencing the userscript is injected (~100 bytes, depending on the length of the `@downloadURL`).

A userscript is injected by reference if and only if it has a specified `@downloadURL` in its metadata.
(This can be overridden using the `--inline` flag, in which case all userscripts are injected inline.)

Userscripts are injected into _every_ response from a matching URL, and the size of a userscript can be anything from a few hundred bytes for the most basic ones to hundreds of kilobytes in extreme cases, so there are _massive_ data usage reductions to be gained from making the userscript accessible by URL and including a `@downloadURL`.
If the `@downloadURL` approach is not possible, for one reason or the other, it is a good idea to be aware of this issue, and to take appropriate action such as [minifying](minification) userscripts and adding suitable ignore rules.


## Userscript compatibility

UP supports (a subset of) the [Greasemonkey metadata syntax](metadata). No adaptation of plain JavaScript userscripts should be required. These directives are supported:

  * `@name`
  * `@version`
  * `@run-at document_(start|end|idle)`
  * `@match`
  * `@include` (basic pattern and regex)
  * `@exclude`
  * `@noframes`
  * `@downloadURL`

The [`GM` API](gm-api) and similar runtime facilities are not supported, because userscripts can only be injected as regular scripts.


## Options

### `--inline`

Always inject scripts inline (`<script>...</script>`), never linked (`<script src="..."></script>`). Useful to test new userscript features without having to re-upload the userscript and clear browser cache.

### `--port PORT`

Make mitmproxy listen to TCP port PORT. Defaults to 8080.

### `--transparent`

Run mitmproxy in [transparent mode](transparent-mode). Useful if you cannot set a proxy in the client. In such cases, you may have to route traffic from the client to the proxy at the network layer instead, making transparent mode necessary.

### `--verbose`

Inject a comment in each page specifying which userscripts (if any) were injected.


[mitmproxy]: https://mitmproxy.org
[minification]: https://en.wikipedia.org/wiki/Minification_(programming)
[metadata]: https://wiki.greasespot.net/Metadata_Block
[transparent-mode]: https://docs.mitmproxy.org/stable/concepts-modes/#transparent-proxy
[gm-api]: https://wiki.greasespot.net/GM.getValue

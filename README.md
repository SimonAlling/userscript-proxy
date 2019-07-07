# Userscript Proxy

Browser extensions on iOS, Android and pretty much any other web browsing device. No jailbreak/root required.

Userscript Proxy is built around [mitmproxy](mitmproxy) and acts as a MITM, injecting matching userscripts into web pages as they flow through it. Both HTTP and HTTPS are supported.


## Security

**Userscript Proxy can (and must be able to) read and modify all HTTP(S) traffic** sent to and from the device in question, so the only reasonably secure way to use it is to run it on a server controlled by oneself.


## Ignoring hosts

Apps like App Store and Facebook Messenger refuse to connect through a MITM proxy, so their traffic must be ignored by mitmproxy. There are two approaches:

  * Blacklisting hosts that cannot connect through the proxy. Tedious, because you have to add exceptions for apps and such all the time.
  * Whitelisting hosts where userscripts should be applied. Works well in general, but does not allow universal userscripts that run on all sites, and the whitelist must be updated when a new userscript is added.

Blacklisting or whitelisting is done by giving the `--ignore` or `--intercept` flag together with one or more files containing **ignore/intercept rules**. Examples:

```bash
# Take ignore rules from ignore.txt (included):
python3.6 launcher.py --ignore "ignore.txt"

# Take intercept rules from all .txt files whose names start with "foo":
python3.6 launcher.py --intercept "foo*.txt"
```

Rules can be specified in two ways:

### Basic pattern

Based on the syntax used by userscript `@include` directives. Asterisk (`*`) means any string (including the empty string). `*.` is automatically prepended. `:*` is automatically appended unless the rule contains a colon (`:`).

To match a domain without matching all of its subdomains, use a regex rule instead (see below).

#### Examples

| Rule           | Matches                                                         |
|----------------|-----------------------------------------------------------------|
| `site.com`     | `site.com` and `x.site.com`                                     |
| `api.site.com` | `api.site.com` and `x.api.site.com`, but not `www.site.com`     |
| `*cdn.net`     | `cdn.net`, `fbcdn.net` and `x.fbcdn.net`, but not `cdn.net.com` |
| `site.com:80`  | `site.com:80` and `x.site.com:80`, but not `site.com:443`       |

### Regular expression

If a rule starts and ends with a slash (`/`), it is treated as a Python regex.

Note that the string to match against contains both a host and a port, e.g. `example.com:443`, and that the regex is used verbatim (i.e. you have to explicitly provide `^` etc if desired). The only exception is that the case-insensitivity flag (`?i`) is automatically added.

Also, be careful with `$`: A regex like `/site.com$/` will never match, because it will only be used to check strings like `site.com:80`.

Anything from a `#` until the end of the line is treated as a comment. Leading and trailing whitespace have no effect.

#### Examples

| Rule            | Matches                                                           |
|-----------------|-------------------------------------------------------------------|
| `/cdn\./`       | `fbcdn.net`, `cdn.site.com`, `cdn.x.site.com`, but not `cdna.com` |
| `/^site\.com:/` | `site.com`, but not `x.site.com`, `mysite.com` or `site.com.net`  |


## Data usage

Userscript Proxy has no data usage impact when no userscript is injected, i.e. for URLs without any matching userscript.
When a script _is_ injected, **exactly one** of the following things happens:

  * The entire userscript is injected as inline JavaScript (potentially dozens or even hundreds of kilobytes).
  * A `<script>` tag referencing the userscript is injected (~100 bytes, depending on the length of the `@downloadURL`).

A userscript is injected by reference if and only if it has a specified `@downloadURL` in its metadata.
(This can be overridden using the `--inline` flag, in which case all userscripts are injected inline.)

Userscripts are injected into _every_ response from a matching URL, and the size of a userscript can be anything from a few hundred bytes for the most basic ones to hundreds of kilobytes in extreme cases, so there are _massive_ data usage reductions to be gained from making the userscript accessible by URL and including a `@downloadURL`.
If the `@downloadURL` approach is not possible, for one reason or the other, it is a good idea to be aware of this issue, and to take appropriate action such as [minifying](minification) userscripts and adding suitable ignore rules.


## Userscript compatibility

Userscript Proxy supports (a subset of) the [Greasemonkey metadata syntax](metadata). No adaptation of plain JavaScript userscripts should be required. These directives are supported:

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

### `--ignore/--intercept FILE`

Take ignore or intercept rules from `FILE`, which can be a glob pattern matching multiple files. `--ignore` and `--intercept` cannot be used together. See examples above.

### `--inline`

Always inject scripts inline (`<script>...</script>`), never linked (`<script src="..."></script>`). Useful to test new userscript features without having to re-upload the userscript and clear browser cache.

### `--list-injected`

Insert an HTML comment in each page specifying which userscripts (if any) were injected.

### `--port PORT`

Make mitmproxy listen to TCP port PORT. Defaults to 8080.

### `--transparent`

Run mitmproxy in [transparent mode](transparent-mode). Useful if you cannot set a proxy in the client. In such cases, you may have to route traffic from the client to the proxy at the network layer instead, making transparent mode necessary.


[mitmproxy]: https://mitmproxy.org
[minification]: https://en.wikipedia.org/wiki/Minification_(programming)
[metadata]: https://wiki.greasespot.net/Metadata_Block
[transparent-mode]: https://docs.mitmproxy.org/stable/concepts-modes/#transparent-proxy
[gm-api]: https://wiki.greasespot.net/GM.getValue

# Userscript Proxy

Browser extensions on iOS, Android and pretty much any other web browsing device.
No jailbreak/root required.

Userscript Proxy is built around [mitmproxy][mitmproxy] and acts as a MITM, injecting userscripts into web pages as they flow through it.
Both HTTP and HTTPS are supported.


# Getting started

## Security notice

Make sure you understand these security aspects before using Userscript Proxy:

  * **You should run the proxy on your own server**, because it can read and modify all traffic sent through it.
  * **You should not expose the proxy to incoming connections from the Internet**, because then anyone can connect to it and use your Internet connection for whatever they want.
    In practice, this means that you should _not_ add a port-forward for Userscript Proxy in your router.
    (Browsing the web via the proxy uses only outgoing connections, which is fine.)

## Starting the proxy

1.  Make sure you have [Docker](https://www.docker.com) installed.
    This should work:

    ```
    docker --version
    ```

1.  Start Userscript Proxy:

    ```
    docker run -t --rm --name userscript-proxy -p 8080:8080 alling/userscript-proxy
    ```

    When you see _Proxy server listening at http://*:8080_, the proxy is up and running.

1.  Check that the proxy is working.
    There are two ways of doing this:

    *   On the command line (in a new terminal):

        ```
        curl --proxy localhost:8080 http://example.com
        ```

        The output should contain a `<script>` element whose first line is `// ==UserScript==`.

    *   In a web browser:

        1.  Go to the preferences menu in your web browser, search for _proxy_ and set `localhost` with port `8080` as HTTP proxy.

        1.  Visit [`http://example.com`](http://example.com).
            You should see a green page and a message saying that Userscript Proxy is working.

## On a mobile device

1.  You need to know the local IP address of the machine running Userscript Proxy (i.e. where you ran `docker run` above).
    This is usually something like `192.168.1.67`.
    You can typically [find it](https://google.com/search?q=find+local+IP+address) by running `ip a`, `ifconfig` or `ipconfig` depending on your operating system.

    If your local IP address is `192.168.1.67`, and the proxy is running (see above), this should work:

    ```
    curl --proxy 192.168.1.67:8080 http://example.com
    ```

1.  Your mobile device needs to be on the same LAN as your proxy, so make sure it's connected to your Wi-Fi.

1.  On your mobile device, go to the settings for the currently active Wi-Fi connection.
    Find the proxy settings, select **Manual proxy** or similar, and set `192.168.1.67` with port `8080`.

1.  Visit [`http://example.com`](http://example.com) on your mobile device.
    You should see the same green page as above.

## HTTPS

When you've set up Userscript Proxy on your mobile device as described above, you'll notice that you can't visit sites via HTTPS anymore.
This is because your device thinks you're being [MITM'd](https://en.wikipedia.org/wiki/Man-in-the-middle_attack) (which, technically, you are – by yourself).

To make HTTPS connections work, you need to tell your device that it should trust your proxy.
This is accomplished by installing a certificate.

**In general, installing a certificate might pose a security risk. If you don't trust me and mitmproxy, stop here.**
Otherwise, read on.

1.  Stop the proxy by pressing `Ctrl` + `C` in the terminal where it's running.
    Then start it again, this time with the `-v` flag as shown below:

    ```
    docker run -t --rm --name userscript-proxy -p 8080:8080 -v "mitmproxy-ca:/root/.mitmproxy" alling/userscript-proxy
    ```

    This creates a new Docker volume and mounts it at `/root/.mitmproxy`, where mitmproxy stores its certificate authority files.
    This is necessary so that you can restart the proxy later without having to perform all these steps again.

    In this example, `mitmproxy-ca` is the name of the new Docker volume.
    You can choose any name you want, as long as it's not already in use.

1.  Make sure your mobile device is configured to use the proxy as decribed above.

1.  On your mobile device, go to [http://mitm.it](http://mitm.it).
    You should see icons for Apple, Windows, Android, etc.

1.  Click the icon matching your device.

1.  Install the certificate.

    ### Android

    Follow the on-screen instructions.
    If you're asked to choose between **VPN and apps** and **Wi-Fi**, choose **VPN and apps**.

    ### iOS

    1.  Tap **Allow** when asked if you want to download a configuration profile.

    1.  Open the Settings app and go to **General** ▶ **Profiles**.

    1.  Under _Downloaded profile_, tap the **mitmproxy** profile.

    1.  Tap **Install** three times.

    1.  Go back to the main screen in Settings and go to **About** ▶ **Certificate Trust Settings**.

    1.  Under _Enable full trust for root certificates_, enable **mitmproxy**, confirming the action if prompted.

1.  You should now be able to browse via HTTPS as usual.

## Deploying userscripts

Userscript Proxy comes with one single userscript, useful only for testing that the proxy is up and running.
To use userscripts you've downloaded or written yourself, you need to tell Userscript Proxy where they are.

1.  You need the **absolute path** to a directory containing your userscripts.
    This could be something like `/home/alling/userscripts`.

1.  Run Userscript Proxy like this:

    ```
    docker run -t --rm --name userscript-proxy -p 8080:8080 -v "mitmproxy-ca:/root/.mitmproxy" -v "/home/alling/userscripts:/userscripts" alling/userscript-proxy --userscripts-dir "/userscripts"
    ```

    *   `-v "/home/alling/userscripts:/userscripts"` mounts your userscripts directory at `/userscripts` inside the Docker container.
    *   `--userscripts-dir "/userscripts"` tells Userscript Proxy to read userscripts from `/userscripts`.


# Apps with certificate pinning

Apps like App Store and Facebook Messenger refuse to connect through a MITM proxy, so their traffic must be ignored by mitmproxy.
There are two approaches:

  * Blacklisting hosts that cannot connect through the proxy.
    Tedious, because you have to add exceptions for apps and such all the time.
  * Whitelisting hosts where userscripts should be applied.
    Works well in general, but does not allow universal userscripts that run on all sites, and the whitelist must be updated when a new userscript is added.

Blacklisting or whitelisting is done by giving the `--rules` flag together with one or more files containing **rules**.
By default, all traffic from hosts matching those rules is ignored (blacklisting); if `--intercept` is given, matching traffic is instead intercepted (whitelisting).

**NOTE:** With `--transparent`, mitmproxy may not be able to see the hostname of responses without intercepting them. In that case, you can only ignore/intercept based on IP address, not hostname.

Examples:

  * Take ignore rules from `/home/alling/rules/ignore.txt`:
    ```bash
    docker run -t --rm -v "/home/alling/rules:/rules" alling/userscript-proxy --rules "/rules/ignore.txt"
    ```
  * Take intercept rules from all `.txt` files in the `/home/alling/rules` directory whose names start with `foo`:
    ```bash
    docker run -t --rm -v "/home/alling/rules:/rules" alling/userscript-proxy --rules "/rules/foo*.txt" --intercept
    ```

Rules can be specified in two ways:

## Basic pattern

Based on the syntax used by userscript `@include` directives.
Asterisk (`*`) means any string (including the empty string).
`*.` is automatically prepended.
`:*` is automatically appended unless the rule contains a colon (`:`).

To match a domain without matching all of its subdomains, use a regex rule instead (see below).

### Examples

| Rule           | Matches                                                         |
|----------------|-----------------------------------------------------------------|
| `site.com`     | `site.com` and `x.site.com`                                     |
| `api.site.com` | `api.site.com` and `x.api.site.com`, but not `www.site.com`     |
| `*cdn.net`     | `cdn.net`, `fbcdn.net` and `x.fbcdn.net`, but not `cdn.net.com` |
| `site.com:80`  | `site.com:80` and `x.site.com:80`, but not `site.com:443`       |

## Regular expression

If a rule starts and ends with a slash (`/`), it is treated as a Python regex.

Note that the string to match against contains both a host and a port, e.g. `example.com:443`, and that the regex is used verbatim (i.e. you have to explicitly provide `^` etc if desired).
The only exception is that the case-insensitivity flag (`?i`) is automatically added.

Also, be careful with `$`: A regex like `/site.com$/` will never match, because it will only be used to check strings like `site.com:80`.

Anything from a `#` until the end of the line is treated as a comment.
Leading and trailing whitespace have no effect.

### Examples

| Rule            | Matches                                                           |
|-----------------|-------------------------------------------------------------------|
| `/cdn\./`       | `fbcdn.net`, `cdn.site.com`, `cdn.x.site.com`, but not `cdna.com` |
| `/^site\.com:/` | `site.com`, but not `x.site.com`, `mysite.com` or `site.com.net`  |


# Data usage

Userscript Proxy has no data usage impact when no userscript is injected, i.e. for URLs without any matching userscript.
When a script _is_ injected, **exactly one** of the following things happens:

  * The entire userscript is injected as inline JavaScript (potentially dozens or even hundreds of kilobytes).
  * A `<script>` tag referencing the userscript is injected (~100 bytes, depending on the length of the `@downloadURL`).

A userscript is injected by reference if and only if it has a specified `@downloadURL` in its metadata.
(This can be overridden using the `--inline` flag, in which case all userscripts are injected inline.)

Userscripts are injected into _every_ response from a matching URL, and the size of a userscript can be anything from a few hundred bytes for the most basic ones to hundreds of kilobytes in extreme cases, so there are _massive_ data usage reductions to be gained from making the userscript accessible by URL and including a `@downloadURL`.
If the `@downloadURL` approach is not possible, for one reason or the other, it is a good idea to be aware of this issue, and to take appropriate action such as [minifying][minification] userscripts and adding suitable ignore rules.


# Userscript compatibility

Userscript Proxy supports (a subset of) the [Greasemonkey metadata syntax][metadata].
No adaptation of plain JavaScript userscripts should be required.
These directives are supported:

  * `@name`
  * `@version`
  * `@run-at document_(start|end|idle)`
  * `@match`
  * `@include` (basic pattern and regex)
  * `@exclude`
  * `@noframes`
  * `@downloadURL`

The [`GM` API][gm-api] and similar runtime facilities are not supported, because userscripts can only be injected as regular scripts.


# Options

Options are specified by simply appending them to the `docker run` command, for example:

```bash
docker run -t --rm --name userscript-proxy -p 8080:8080 alling/userscript-proxy --transparent
#          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                         ^^^^^^^^^^^^^
#          flags to `docker run`                                                flags to Userscript Proxy
```

## `--bypass-csp ALLOW`

Bypass host site's Content Security Policy (if any) to allow userscripts to run properly.
If `ALLOW` is `script`, the CSP is bypassed only for the userscript itself.
Use `nothing` to never bypass any CSP (meaning userscripts won't work at all on some sites).
Use `everything` to allow everything, which may be necessary if the userscript injects CSS, images etc.
Note that the latter completely disables any CSP from every host site into which a userscript is injected.
Defaults to `script`.

## `--inline`, `-i`

Always inject scripts inline (`<script>...</script>`), never linked (`<script src="..."></script>`).
Useful to test new userscript features without having to re-upload the userscript and clear browser cache.

## `--list-injected`, `-l`

Insert an HTML comment in each page specifying which userscripts (if any) were injected.

## `--no-default-rules`

Skip built-in default rules, which are otherwise automatically applied so that common apps like App Store and Facebook Messenger work out of the box.

## `--no-default-userscripts`

Skip loading built-in default userscripts intended for sanity checks and similar purposes, e.g. Example Userscript.

## `--port PORT`, `-p PORT`

Make mitmproxy listen to TCP port `PORT`.
Defaults to `8080`.

**Note:** Be careful when running Userscript Proxy in Docker! If you want to use e.g. port 1337 on the host machine, do this instead:

```bash
docker run -t --rm --name userscript-proxy -p 1337:8080 alling/userscript-proxy
```

If you really want Userscript Proxy to use a certain port _inside_ the Docker container, e.g. 5555, don't forget to publish that port:

```bash
docker run -t --rm --name userscript-proxy -p 1337:5555 alling/userscript-proxy -p 5555
```

Or you can let the Docker container be a part of the host's network:

```bash
docker run -t --rm --network host --name userscript-proxy alling/userscript-proxy -p 5555
```

## `--query-param-to-disable PARAM`, `-q PARAM`

Disable userscripts when the request URL contains `PARAM` as a query parameter.
For example, use `-q foo` to disable userscripts for `http://example.com?foo`.
Defaults to `nouserscripts`.

## `--rules FILE`

Take ignore or intercept rules from `FILE`, which can be a glob pattern matching multiple files.
By default, matching traffic is ignored; use `--intercept` to invert this behavior.
See examples above.

## `--transparent`, `-t`

Run mitmproxy in [transparent mode][transparent-mode].
Useful if you cannot set a proxy in the client, e.g. when using OpenVPN Connect on Android to connect to a VPN server on the network where your proxy is running.
In such cases, you have to route traffic from the client to the proxy at the network layer instead, making transparent mode necessary.

**NOTE:** In transparent mode, ignore/intercept rules based on hostname (rather than IP address) may not work, because mitmproxy may not be able to see the hostname of responses without intercepting them.

## `--userscripts-dir DIR`, `-u DIR`

Load userscripts from directory `DIR`.


# Contribute

How to build and run from source:

```
git clone https://github.com/SimonAlling/userscript-proxy
cd userscript-proxy
make start
```


[mitmproxy]: https://mitmproxy.org
[minification]: https://en.wikipedia.org/wiki/Minification_(programming)
[metadata]: https://wiki.greasespot.net/Metadata_Block
[transparent-mode]: https://docs.mitmproxy.org/stable/concepts-modes/#transparent-proxy
[gm-api]: https://wiki.greasespot.net/GM.getValue

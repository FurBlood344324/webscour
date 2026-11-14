![Got](https://github.com/sindresorhus/media/logo.svg)

---

Sindre's open source work is supported by the community.
Special thanks to:

![Fame Helsinki](https://camo.githubusercontent.com/8bd942dbf382e3842da490d2f1c321cc55dde6a53fe2d1e6d9cc719fed2852db/68747470733a2f2f73696e647265736f726875732e636f6d2f6173736574732f7468616e6b732f66616d652d6c6f676f2d6c696768742e737667)   ![Fame Helsinki](https://camo.githubusercontent.com/84cdf40d1d2e04cdaf3a2082ecce4f33ec36e52c96e6e8f00002dfd5acd7c7f5/68747470733a2f2f73696e647265736f726875732e636f6d2f6173736574732f7468616e6b732f66616d652d6c6f676f2d6461726b2e737667)          **Fast remote container builds and GitHub Actions runners.**

---

> Human-friendly and powerful HTTP request library for Node.js

[![Downloads](https://camo.githubusercontent.com/d7976e0bda297ef5c62139d8ef779ff13c47192f5c71be2dac45252c734432bd/68747470733a2f2f696d672e736869656c64732e696f2f6e706d2f646d2f676f742e737667)](https://npmjs.com/got) [![Install size](https://camo.githubusercontent.com/f07865810db1dfe04d784b113f03bb301d84393a7fbb35dca31450d758592441/68747470733a2f2f7061636b61676570686f6269612e636f6d2f62616467653f703d676f74)](https://packagephobia.com/result?p=got)

[See how Got compares to other HTTP libraries](https://github.com/sindresorhus/got#comparison)

---

**You probably want [Ky](https://github.com/sindresorhus/ky) instead, by the same people. It's smaller, works in the browser too, and is more stable since it's built on [`Fetch`](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API). Or [fetch-extras](https://github.com/sindresorhus/fetch-extras) for simple needs.**

---

**Support questions should be asked [here](https://github.com/sindresorhus/got/discussions).**

## Install

```
npm install got
```

**Warning:** This package is native [ESM](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules) and no longer provides a CommonJS export. If your project uses CommonJS, you will have to [convert to ESM](https://gist.github.com/sindresorhus/a39789f98801d908bbc7ff3ecc99d99c). Please don't open issues for questions regarding CommonJS / ESM.

**Got v11 is no longer maintained and we will not accept any backport requests.**

## Take a peek

**A [quick start](https://github.com/sindresorhus/documentation/quick-start.md) guide is available.**

### JSON mode

Got has a dedicated option for handling JSON payload.
Furthermore, the promise exposes a `.json<T>()` function that returns `Promise<T>`. It also exposes a `.json(schema)` function that validates the payload with a [Standard Schema](https://standardschema.dev) and infers the type from the schema.

```
import got from 'got';

const {data} = await got.post('https://httpbin.org/anything', {
	json: {
		hello: 'world'
	}
}).json();

console.log(data);
//=> {"hello": "world"}
```

For advanced JSON usage, check out the [`parseJson`](https://github.com/sindresorhus/documentation/2-options.md#parsejson) and [`stringifyJson`](https://github.com/sindresorhus/documentation/2-options.md#stringifyjson) options.

**For more useful tips like this, visit the [Tips](https://github.com/sindresorhus/documentation/tips.md) page.**

## Highlights

## Documentation

By default, Got will retry on failure. To disable this option, set [`options.retry.limit`](https://github.com/sindresorhus/documentation/7-retry.md#retry) to 0.

#### Main API

- Promise API
- Options
- Stream API
- Pagination API
- Advanced HTTPS API
- HTTP/2 support
- `Response` class
- Response validation with Standard Schema

#### Timeouts and retries

#### Advanced creation

#### Cache, Proxy and UNIX sockets

#### Integration

---

### Migration guides

## Got plugins

- `got4aws` - Got convenience wrapper to interact with AWS v4 signed APIs
- `gh-got` - Got convenience wrapper to interact with the GitHub API
- `gl-got` - Got convenience wrapper to interact with the GitLab API
- `gotql` - Got convenience wrapper to interact with GraphQL using JSON-parsed queries instead of strings
- `got-fetch` - Got with a `fetch` interface
- `got-scraping` - Got wrapper specifically designed for web scraping purposes
- `got-ssrf` - Got wrapper to protect server-side requests against SSRF attacks

## Comparison

`got` [`node-fetch`](https://github.com/node-fetch/node-fetch) [`ky`](https://github.com/sindresorhus/ky) [`axios`](https://github.com/axios/axios) [`superagent`](https://github.com/visionmedia/superagent)     HTTP/2 support ✔️ ❌ ✔️ ❌ ✔️**   Browser support ❌ ✔️* ✔️ ✔️ ✔️   Promise API ✔️ ✔️ ✔️ ✔️ ✔️   Stream API ✔️ Node.js only ❌ ❌ ✔️   Pagination API ✔️ ❌ ❌ ❌ ❌   Request aborting ✔️ ✔️ ✔️ ✔️ ✔️   RFC 7234 caching ✔️ ❌ ❌ ❌ ❌   Cookies (out-of-the-box) ✔️ ❌ ❌ ❌ ❌   Follows redirects ✔️ ✔️ ✔️ ✔️ ✔️   Retries on failure ✔️ ❌ ✔️ ❌ ✔️   Progress events ✔️ ❌ ✔️ Browser only ✔️   Handles gzip/deflate ✔️ ✔️ ✔️ ✔️ ✔️   Advanced timeouts ✔️ ❌ ❌ ❌ ❌   Timings ✔️ ❌ ❌ ❌ ❌   Errors with metadata ✔️ ❌ ✔️ ✔️ ❌   JSON mode ✔️ ✔️ ✔️ ✔️ ✔️   Custom defaults ✔️ ❌ ✔️ ✔️ ❌   Composable ✔️ ❌ ❌ ❌ ✔️   Hooks ✔️ ❌ ✔️ ✔️ ❌   Issues open [![](https://camo.githubusercontent.com/98dc279d0489637e899b182290060ab7647f482357fe59e32a7b979477bc8590/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d7261772f73696e647265736f726875732f676f743f636f6c6f723d67726179266c6162656c)](https://github.com/sindresorhus/got/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc) [![](https://camo.githubusercontent.com/60de0b971c457da6839e916b9b2ab881a075660b889ffd3e82b394ee28b33e3b/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d7261772f626974696e6e2f6e6f64652d66657463683f636f6c6f723d67726179266c6162656c)](https://github.com/bitinn/node-fetch/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc) [![](https://camo.githubusercontent.com/540af5ad2e1f71f4e4941d9a328807c2afbe4455d1d5d55b837b00d8bef95b0f/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d7261772f73696e647265736f726875732f6b793f636f6c6f723d67726179266c6162656c)](https://github.com/sindresorhus/ky/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc) [![](https://camo.githubusercontent.com/f873ce12bbb578679c1ae0b59f9a4e07c087a6c2a26948b0bcacd0b23bc75f46/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d7261772f6178696f732f6178696f733f636f6c6f723d67726179266c6162656c)](https://github.com/axios/axios/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc) [![](https://camo.githubusercontent.com/f48cc5b657eef26826ee3cdd79296df44130896d80829df31d630bdf9cfeb797/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d7261772f766973696f6e6d656469612f73757065726167656e743f636f6c6f723d67726179266c6162656c)](https://github.com/visionmedia/superagent/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc)   Issues closed [![](https://camo.githubusercontent.com/eedcb6fcf6d6b2c1aa66c6fc98fae1d239dd41368542771544364cc4cebf8911/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d636c6f7365642d7261772f73696e647265736f726875732f676f743f636f6c6f723d626c7565266c6162656c)](https://github.com/sindresorhus/got/issues?q=is%3Aissue+is%3Aclosed+sort%3Aupdated-desc) [![](https://camo.githubusercontent.com/9630db6cbdc6c03dc694dd1f2eca47ece81285ba2ddba33fa6741568309715ca/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d636c6f7365642d7261772f626974696e6e2f6e6f64652d66657463683f636f6c6f723d626c7565266c6162656c)](https://github.com/bitinn/node-fetch/issues?q=is%3Aissue+is%3Aclosed+sort%3Aupdated-desc) [![](https://camo.githubusercontent.com/d6272e490db029f0655c22b6a44594e6dbc236b5479ca9a413688233fc5b7e06/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d636c6f7365642d7261772f73696e647265736f726875732f6b793f636f6c6f723d626c7565266c6162656c)](https://github.com/sindresorhus/ky/issues?q=is%3Aissue+is%3Aclosed+sort%3Aupdated-desc) [![](https://camo.githubusercontent.com/72be2fd7c1d0951c8086b45706cff57cd522ee09dced08d86f250a61d10d9b9c/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d636c6f7365642d7261772f6178696f732f6178696f733f636f6c6f723d626c7565266c6162656c)](https://github.com/axios/axios/issues?q=is%3Aissue+is%3Aclosed+sort%3Aupdated-desc) [![](https://camo.githubusercontent.com/b9e03383fc01a59fb1e7270d3dfb15fbfaa5283544baba3b00f20a4d575a6982/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d636c6f7365642d7261772f766973696f6e6d656469612f73757065726167656e743f636f6c6f723d626c7565266c6162656c)](https://github.com/visionmedia/superagent/issues?q=is%3Aissue+is%3Aclosed+sort%3Aupdated-desc)   Downloads [![](https://camo.githubusercontent.com/49bb164430f8cf09925e56a000569057f40a8fda055dbc0ffd3629e755e8394f/68747470733a2f2f696d672e736869656c64732e696f2f6e706d2f646d2f676f743f636f6c6f723d6461726b677265656e266c6162656c)](https://www.npmjs.com/package/got) [![](https://camo.githubusercontent.com/ccc4475eb1f6766a2fb13476d82f40ce2812b6172442a933ba4576a8e6949ab8/68747470733a2f2f696d672e736869656c64732e696f2f6e706d2f646d2f6e6f64652d66657463683f636f6c6f723d6461726b677265656e266c6162656c)](https://www.npmjs.com/package/node-fetch) [![](https://camo.githubusercontent.com/9767891566a54c302455dfefa4170d445b8ba8de54e8e745f980587257704c30/68747470733a2f2f696d672e736869656c64732e696f2f6e706d2f646d2f6b793f636f6c6f723d6461726b677265656e266c6162656c)](https://www.npmjs.com/package/ky) [![](https://camo.githubusercontent.com/9eaa99e725bdfa39545a4a687107f36bf6672a77bf3d8a9bca842d6914909886/68747470733a2f2f696d672e736869656c64732e696f2f6e706d2f646d2f6178696f733f636f6c6f723d6461726b677265656e266c6162656c)](https://www.npmjs.com/package/axios) [![](https://camo.githubusercontent.com/91384aac196e01af666c5f68ac08fb0adcc853e786547da6c917e3930f1f5dab/68747470733a2f2f696d672e736869656c64732e696f2f6e706d2f646d2f73757065726167656e743f636f6c6f723d6461726b677265656e266c6162656c)](https://www.npmjs.com/package/superagent)   Coverage TBD [![](https://camo.githubusercontent.com/ea7f10ac6228e3213657690d0d7ef74c3b1a69284ee4de3c47900de9b91ac801/68747470733a2f2f696d672e736869656c64732e696f2f636f766572616c6c732f6769746875622f626974696e6e2f6e6f64652d66657463683f636f6c6f723d306239303632266c6162656c)](https://coveralls.io/github/bitinn/node-fetch) [![](https://camo.githubusercontent.com/86b966dc33a5b297b9d7e784a47ed189ad936871962575f2e728d46830bbdde5/68747470733a2f2f696d672e736869656c64732e696f2f636f6465636f762f632f6769746875622f73696e647265736f726875732f6b793f636f6c6f723d306239303632266c6162656c)](https://codecov.io/gh/sindresorhus/ky) [![](https://camo.githubusercontent.com/4fd950c7cc80a74296ddd8d97f1d7dfc5c631cff1a8908c673773650a8e894c1/68747470733a2f2f696d672e736869656c64732e696f2f636f766572616c6c732f6769746875622f6d7a61627269736b69652f6178696f733f636f6c6f723d306239303632266c6162656c)](https://coveralls.io/github/mzabriskie/axios) [![](https://camo.githubusercontent.com/d19bba7b091b2f39123c99d311a260feae2c02c4bd3f461ac5fe8ba716cef9b3/68747470733a2f2f696d672e736869656c64732e696f2f636f6465636f762f632f6769746875622f766973696f6e6d656469612f73757065726167656e743f636f6c6f723d306239303632266c6162656c)](https://codecov.io/gh/visionmedia/superagent)   Build [![](https://github.com/sindresorhus/got/actions/workflows/main.yml/badge.svg)](https://github.com/sindresorhus/got/actions/workflows/main.yml) [![](https://camo.githubusercontent.com/bde2daf7ee6a755cbe9f1be68c6cb236d7956679d4cfa92a593058312e85e03e/68747470733a2f2f696d672e736869656c64732e696f2f7472617669732f626974696e6e2f6e6f64652d66657463683f6c6162656c)](https://travis-ci.org/github/bitinn/node-fetch) [![](https://github.com/sindresorhus/ky/actions/workflows/main.yml/badge.svg)](https://github.com/sindresorhus/ky/actions/workflows/main.yml) [![](https://camo.githubusercontent.com/68f4c4876a67474c25bc2aae5824f7dc3105cee65d05c90623fb3183f9a4ce45/68747470733a2f2f696d672e736869656c64732e696f2f7472617669732f6178696f732f6178696f733f6c6162656c)](https://travis-ci.org/github/axios/axios) [![](https://camo.githubusercontent.com/8c42fb70aea3ffc0264411bca545d59f0a9003964db3cb974a22049a80fd86ce/68747470733a2f2f696d672e736869656c64732e696f2f7472617669732f766973696f6e6d656469612f73757065726167656e743f6c6162656c)](https://travis-ci.org/github/visionmedia/superagent)   Bugs [![](https://camo.githubusercontent.com/99d0e4b32350f1de1e32c59e8e9a01e8c2c0bd9c69430d2933baa3a069267d70/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d7261772f73696e647265736f726875732f676f742f6275673f636f6c6f723d6461726b726564266c6162656c)](https://github.com/sindresorhus/got/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc+label%3Abug) [![](https://camo.githubusercontent.com/9122bdfc713601baffbd3a93c61d6a7b9e142171e3dd0f86f30142eb57d3c6c3/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d7261772f626974696e6e2f6e6f64652d66657463682f6275673f636f6c6f723d6461726b726564266c6162656c)](https://github.com/bitinn/node-fetch/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc+label%3Abug) [![](https://camo.githubusercontent.com/f7ade826092e8ec5702174a8813edc97ab60077a86acf405420e56cbe9cda8a3/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d7261772f73696e647265736f726875732f6b792f6275673f636f6c6f723d6461726b726564266c6162656c)](https://github.com/sindresorhus/ky/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc+label%3Abug) [![](https://camo.githubusercontent.com/8f26676041bb3890080d86b6093b13a7c874d83cdefa68de34387a26f4ab3a93/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d7261772f6178696f732f6178696f732f6275672d6669783f636f6c6f723d6461726b726564266c6162656c)](https://github.com/axios/axios/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc+label%3A%22bug-fix%22) [![](https://camo.githubusercontent.com/5e8f1d7983a3c396b02c829ecc4caa1a285bec0a49fd97179a165388ff0e13e1/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732d7261772f766973696f6e6d656469612f73757065726167656e742f4275673f636f6c6f723d6461726b726564266c6162656c)](https://github.com/visionmedia/superagent/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc+label%3ABug)   Dependents [![](https://camo.githubusercontent.com/cc7e39a853fd4d2411bdd191b665e6f39e88654c36a51193feae00af53d48490/68747470733a2f2f62616467656e2e6e65742f6e706d2f646570656e64656e74732f676f743f636f6c6f723d6f72616e6765266c6162656c)](https://www.npmjs.com/package/got?activeTab=dependents) [![](https://camo.githubusercontent.com/24ac70688be3be3448b094be341e87213072cce2642d7ab8e1f4f17a642f67cd/68747470733a2f2f62616467656e2e6e65742f6e706d2f646570656e64656e74732f6e6f64652d66657463683f636f6c6f723d6f72616e6765266c6162656c)](https://www.npmjs.com/package/node-fetch?activeTab=dependents) [![](https://camo.githubusercontent.com/3a6442e634f9fb9f2a8569a5d7cae1c9d5a14c1b4a02dc2302e0864912130359/68747470733a2f2f62616467656e2e6e65742f6e706d2f646570656e64656e74732f6b793f636f6c6f723d6f72616e6765266c6162656c)](https://www.npmjs.com/package/ky?activeTab=dependents) [![](https://camo.githubusercontent.com/1b5bca91bdc9cf403cecd683c73bb98ff41817dcd98b9320c3cefcd213f6af53/68747470733a2f2f62616467656e2e6e65742f6e706d2f646570656e64656e74732f6178696f733f636f6c6f723d6f72616e6765266c6162656c)](https://www.npmjs.com/package/axios?activeTab=dependents) [![](https://camo.githubusercontent.com/10869adb8c5840f09d06e0ed608ba713a491b5f4208485a3bd2ea71bc255ee1b/68747470733a2f2f62616467656e2e6e65742f6e706d2f646570656e64656e74732f73757065726167656e743f636f6c6f723d6f72616e6765266c6162656c)](https://www.npmjs.com/package/visionmedia?activeTab=dependents)   Install size [![](https://camo.githubusercontent.com/f07865810db1dfe04d784b113f03bb301d84393a7fbb35dca31450d758592441/68747470733a2f2f7061636b61676570686f6269612e636f6d2f62616467653f703d676f74)](https://packagephobia.com/result?p=got) [![](https://camo.githubusercontent.com/3441cf4012e2d5edf19f55d32bbc03a424d114b115bfc23025ae1604ee80cf37/68747470733a2f2f7061636b61676570686f6269612e636f6d2f62616467653f703d6e6f64652d6665746368)](https://packagephobia.com/result?p=node-fetch) [![](https://camo.githubusercontent.com/15a1d784f5b29c0bff6e780b401cb065f6114996795a72607b34a869abf0a2e7/68747470733a2f2f7061636b61676570686f6269612e636f6d2f62616467653f703d6b79)](https://packagephobia.com/result?p=ky) [![](https://camo.githubusercontent.com/4d06216d09009dafb03912ae927d36ad3595d4e563a7ed79eb4a7a779b60188f/68747470733a2f2f7061636b61676570686f6269612e636f6d2f62616467653f703d6178696f73)](https://packagephobia.com/result?p=axios) [![](https://camo.githubusercontent.com/3aa8c98b44ed27a0ae94900a3672aca4bfccf3c7688b084b1100e3448d4f3ae1/68747470733a2f2f7061636b61676570686f6269612e636f6d2f62616467653f703d73757065726167656e74)](https://packagephobia.com/result?p=superagent)   GitHub stars [![](https://camo.githubusercontent.com/c21a50741c0820d42aca6c07ee25fa8af9795acd83f5da03ee972dfad11e76e1/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73746172732f73696e647265736f726875732f676f743f636f6c6f723d7768697465266c6162656c)](https://github.com/sindresorhus/got) [![](https://camo.githubusercontent.com/574910f9911de797374231d6f04707b6af2dff7427f8b46dd14614f8808f07bb/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73746172732f626974696e6e2f6e6f64652d66657463683f636f6c6f723d7768697465266c6162656c)](https://github.com/node-fetch/node-fetch) [![](https://camo.githubusercontent.com/fc82e7f6c08f39831ac7f1f80bc35619f3c3f8a9293447d268bc579cb1b2365d/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73746172732f73696e647265736f726875732f6b793f636f6c6f723d7768697465266c6162656c)](https://github.com/sindresorhus/ky) [![](https://camo.githubusercontent.com/14e4a678ba962a2de59dd7fc23358ef845e6c1cb5a8dd0d5d06427433f8b4b90/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73746172732f6178696f732f6178696f733f636f6c6f723d7768697465266c6162656c)](https://github.com/axios/axios) [![](https://camo.githubusercontent.com/ecb29f939568daa9fa5011ab0cd49e6a4992bf03010f0d2ec4e5cc40880218b3/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73746172732f766973696f6e6d656469612f73757065726167656e743f636f6c6f723d7768697465266c6162656c)](https://github.com/visionmedia/superagent)   TypeScript support [![](https://camo.githubusercontent.com/a3d5e1fc547affe4893e5b1ecb475ef0f5216d5c171c6c4a1b72b24f965a859e/68747470733a2f2f62616467656e2e6e65742f6e706d2f74797065732f676f743f6c6162656c)](https://github.com/sindresorhus/got) [![](https://camo.githubusercontent.com/9f4c746776934aba6dd8fde00266cfe0372c79eb675c86d94328c105e275d743/68747470733a2f2f62616467656e2e6e65742f6e706d2f74797065732f6e6f64652d66657463683f6c6162656c)](https://github.com/node-fetch/node-fetch) [![](https://camo.githubusercontent.com/84fa3b7894bdf4b3bf5dbfc006e24eaa9ba1b2f581c6250724cacaef24d46452/68747470733a2f2f62616467656e2e6e65742f6e706d2f74797065732f6b793f6c6162656c)](https://github.com/sindresorhus/ky) [![](https://camo.githubusercontent.com/3b175ed5f1cc9dc880d384990b6d3806cbec999b7c78184dd20032c5c4e320d4/68747470733a2f2f62616467656e2e6e65742f6e706d2f74797065732f6178696f733f6c6162656c)](https://github.com/axios/axios) [![](https://camo.githubusercontent.com/f1951d9e8a1e86186b1cdf030b46c69a0ae7659d6d7de7f9af422c9392a8ddf1/68747470733a2f2f62616467656e2e6e65742f6e706d2f74797065732f73757065726167656e743f6c6162656c)](https://github.com/visionmedia/superagent/commits)   Last commit [![](https://camo.githubusercontent.com/a58bfa5e2a5797abf049e3540972137a78697ecc9f84c9960cbda5e23eb91b51/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c6173742d636f6d6d69742f73696e647265736f726875732f676f743f636f6c6f723d67726179266c6162656c)](https://github.com/sindresorhus/got/commits) [![](https://camo.githubusercontent.com/567574da1da98c5bbe6fdc5b6939fbda47f35e78fa992545d33879c49645740e/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c6173742d636f6d6d69742f626974696e6e2f6e6f64652d66657463683f636f6c6f723d67726179266c6162656c)](https://github.com/node-fetch/node-fetch/commits) [![](https://camo.githubusercontent.com/fd576587f87af37c0068bab6c14091baefe6cd0785241b7e0dbfea0e5c070a19/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c6173742d636f6d6d69742f73696e647265736f726875732f6b793f636f6c6f723d67726179266c6162656c)](https://github.com/sindresorhus/ky/commits) [![](https://camo.githubusercontent.com/7fa63716a3a61da8314c49af729f9acc2cd3a3a796bbe96799c93e21e9f16768/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c6173742d636f6d6d69742f6178696f732f6178696f733f636f6c6f723d67726179266c6162656c)](https://github.com/axios/axios/commits) [![](https://camo.githubusercontent.com/1bddbd122abc023f2da60e5ca848db79c5e9b971bfee4513b232f292373bb561/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c6173742d636f6d6d69742f766973696f6e6d656469612f73757065726167656e743f636f6c6f723d67726179266c6162656c)](https://github.com/visionmedia/superagent/commits)

\* It's almost API compatible with the browser `fetch` API.
** Need to switch the protocol manually. Doesn't accept PUSH streams and doesn't reuse HTTP/2 sessions.
❇️ Almost-stable feature, but the API may change. Don't hesitate to try it out!
❔ Feature in early stage of development. Very experimental.

[Click here](https://packagephobia.com/result?p=@sindresorhus/is@8.0.0,byte-counter@0.1.0,cacheable-request@13.0.18,chunk-data@0.1.0,decompress-response@10.0.0,keyv@5.6.0,lowercase-keys@4.0.1,responselike@4.0.2,type-fest@5.6.0,uint8array-extras@1.5.0) to see the install size of the Got dependencies.

## Maintainers

[![Sindre Sorhus](https://github.com/sindresorhus.png?size=100)](https://sindresorhus.com) [![Szymon Marczak](https://github.com/szmarczak.png?size=100)](https://github.com/szmarczak)     [Sindre Sorhus](https://sindresorhus.com) [Szymon Marczak](https://github.com/szmarczak)

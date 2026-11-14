Skip to content

# Deploy your framework on Vercel

Build with Next.js, SvelteKit, Nuxt, Hono, FastAPI, or another supported framework. Vercel detects your framework and configures the build for you, often with no setup.

app/api/hello/route.ts

```
import { NextResponse } from 'next/server';
 
// Next.js serves this file at /api/hello.
export async function GET() {
  const message = 'Hello from Next.js!';
  return NextResponse.json({ message });
}
```

src/routes/api/hello/+server.ts

```
import { json } from '@sveltejs/kit';
 
// SvelteKit serves this file at /api/hello.
export function GET() {
  const message = 'Hello from SvelteKit!';
  return json({ message });
}
```

server/api/hello.ts

```
// Nuxt auto-imports defineEventHandler.
 
// Nuxt serves this file at /api/hello.
export default defineEventHandler(() => {
  const message = 'Hello from Nuxt!';
  return { message };
});
```

src/index.ts

```
import { Hono } from 'hono';
 
const app = new Hono();
const message = 'Hello from Hono!';
app.get('/api/hello', (c) => c.json({ message }));
 
export default app;
```

main.py

```
from fastapi import FastAPI
 
app = FastAPI()
 
@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI!"}
```

Each example serves the same `/api/hello` endpoint using the framework's own conventions. The files contain no Vercel-specific code. Vercel detects the framework when you deploy and configures the build for it.

Vercel has first-class support for [a wide range of the most popular frameworks](https://vercel.com/docs/frameworks/more-frameworks). You can build and deploy using frontend, backend, and full-stack frameworks ranging from SvelteKit to Nitro, often without any upfront configuration.

For AI applications, explore [agent frameworks](https://vercel.com/docs/frameworks/agents) to build agents with eve, Mastra, Flue, and Vercel. Each guide covers the framework’s setup, hosting requirements, and Vercel integrations.

Use the [web applications reference architecture](https://vercel.com/kb/architecture/web) to choose a framework and rendering approach, then plan data access, authentication, and caching.

Learn how to [get started with Vercel](https://vercel.com/docs/getting-started-with-vercel) or clone one of our example repos to your favorite git provider and deploy it on Vercel using one of the templates below:

Get started in minutes

## Deploy a Template

Vercel deployments can [integrate with your git provider](https://vercel.com/docs/git) to [generate preview URLs](https://vercel.com/docs/deployments/environments#preview-environment-pre-production) for each pull request you make to your project.

Deploying on Vercel with one of our [supported frameworks](https://vercel.com/docs/frameworks/more-frameworks) gives you access to many features, such as:

- Vercel Functions enable developers to write functions that scale based on traffic demands, preventing failures during peak hours and reducing costs during low activity.
- Middleware is code that executes before a request is processed on a site, enabling you to modify the response. Because it runs before the cache, Middleware is an effective way to personalize statically generated content.
- Multi-runtime Support allows the use of various runtimes for your functions, each with unique libraries, APIs, and features tailored to different technical requirements.
- Incremental Static Regeneration enables content updates without redeployment. Vercel caches the page to serve it statically and rebuilds it on a specified interval.
- Speed Insights provide data on your project's Core Web Vitals performance in the Vercel dashboard, helping you improve loading speed, responsiveness, and visual stability.
- Analytics offer detailed insights into your website's performance over time, including metrics like top pages, top referrers, and user demographics.
- Skew Protection uses version locking to ensure that the client and server use the same version of your application, preventing version skew and related errors.

The following table shows which features are supported by each framework on Vercel. The framework list represents the most popular frameworks deployed on Vercel.

Supported

Not Supported

Not Applicable

| Feature | Next.js | SvelteKit | Nuxt | TanStack | Astro | Remix | Vite | CRA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

No rows displayed.

The [Build Output API](https://vercel.com/docs/build-output-api) is a file-system-based specification for a directory structure that produces a Vercel deployment. It is primarily targeted at framework authors who want to integrate their frameworks with Vercel's platform features. By implementing this directory structure as the output of their build command, framework authors can utilize all Vercel platform features, such as Vercel Functions, Routing, and Caching.

If you are not using a framework, you can still use these features by manually creating and populating the `.vercel/output` directory according to this specification. Complete examples of Build Output API directories can be found in [vercel/examples](https://github.com/vercel/examples/tree/main/build-output-api), and you can read our [blog post](https://vercel.com/blog/build-your-own-web-framework) on using the Build Output API to build your own framework with Vercel.

Learn more about deploying your preferred framework on Vercel with the following resources:

---

Was this helpful?

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### AI Agent (local backend)

The home page includes a "Validate with AI" panel (Flesh out, Refine, Rank). It calls the Remand backend through same-origin Next.js API routes.

For local dev, run the backend on port 8000:

```bash
cd backend && python -m uvicorn main:app --reload
```

Set frontend env vars in `frontend/.env.local`:

```bash
# Preferred: server-only backend URL used by /api/* route handlers
API_URL=http://localhost:8000

# Optional for SSR or direct backend calls (avoid in production to prevent mixed content)
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Production (Vercel)**

- Set **`API_URL`** in Project Settings → Environment Variables (e.g. `http://51.83.42.203`). This is used only by Next.js API route handlers on the server.
- **Remove `NEXT_PUBLIC_API_URL`** from Production (and Preview unless needed). Leaving it set can cause the browser to call the backend directly and trigger mixed-content blocking (HTTPS page → HTTP backend).
- Redeploy with **cleared build cache** if you previously had `NEXT_PUBLIC_API_URL` set, so the bundle does not keep using the old client-side base URL.
- Browser flows (AI Enhance, engage, search top-matches) call same-origin `/api/*` routes, which then call the backend using `API_URL`.

**Security**

- Do not put provider API keys (e.g. Anthropic) in `frontend/.env.local` or any frontend env that might be committed or shared. Keep secrets in backend/server env only. If a key was ever committed or exposed, rotate it.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

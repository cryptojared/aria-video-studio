# Aria UGC (UGCMP) — Launch Checklist

## Status: Ready for Launch 🚀

**Backend:** https://ugcmparia-production.up.railway.app  
**Frontend:** https://ugc-manager-pro-v1.netlify.app  
**Domain:** ariaugc.com

---

## Pre-Launch Tasks

### 1. Rotate Exposed Credentials ⚠️
- [ ] Rotate OpenAI API key (currently hardcoded in repo)
- [ ] Rotate MiniMax API key (currently hardcoded in repo)
- [ ] Update Supabase keys in Railway env vars
- [ ] Verify no other keys exposed in JS files

### 2. Deploy Frontend to Netlify
- [ ] Build frontend: `cd ~/ugcmp-build/aria-web && npm run build`
- [ ] Deploy to Netlify
- [ ] Or: Connect GitHub repo for auto-deploy

### 3. DNS Configuration
- [ ] Point ariaugc.com to Netlify (or Railway)
- [ ] Verify SSL certificate
- [ ] Test custom domain

### 4. Database Migration
- [ ] Apply subscription fields migration to Supabase
- [ ] Verify all tables have correct RLS policies

### 5. Stripe Integration
- [ ] Create Stripe webhook endpoint: `https://ariaugc.com/billing/webhook`
- [ ] Test checkout flow end-to-end
- [ ] Verify webhook events: `checkout.session.completed`, `customer.subscription.updated`

### 6. Launch Smoke Test
- [ ] Sign up new user
- [ ] Create a project
- [ ] Add contacts
- [ ] Create an invoice
- [ ] Test chat with Aria
- [ ] Verify Stripe checkout works

---

## Known Issues (Fix Before Launch)

1. **Hardcoded userId** — AI chat saves to fake user (`userId='demo-user'`)
2. **Dashboard stats** — Hardcoded values, not real data
3. **Files/Products/Invoices pages** — No Supabase integration yet
4. **API keys exposed** — Need to rotate before going live

---

## Post-Launch

- [ ] Monitor Railway logs for errors
- [ ] Track Stripe webhooks
- [ ] Gather user feedback
- [ ] Plan V2 features (Aria Video Studio!)

---

*Last updated: 2026-10-06*

# Accounts and Users

Boxes separates **billing accounts** from **login users**. They are managed together under **Management → Accounts and Users** (one menu item; Accounts tab and Users tab on the page).

## Concepts

| Term | Meaning |
|------|---------|
| **Account** | Billing and parcel entity: balance, packages, ledger, Stripe customer, aliases. |
| **User (CustomUser)** | Login identity: username, password, profile, groups (Staff, Customer, Delivery, Admin). |
| **Membership (UserAccount)** | Optional link between a user and an account, with a **role**. |

`Account.user` is the **creator** of the account row (often staff or the system user). It is **not** the customer portal membership — use `UserAccount` for that.

## Roles: Owner vs Member

Both roles get the **same customer portal access** for that account (parcels, payments, invoices, ledger). The difference is operational and staff-facing:

| | **Owner** | **Member** |
|---|-----------|------------|
| Portal access | Full for linked account | Full for linked account |
| Meaning | Primary contact for the billing account | Additional login on the same account |
| Unlink | Cannot unlink the **last active owner** without override | Can be unlinked freely |
| Demote | Cannot demote the last active owner without override | N/A |

Change roles anytime from:

- Account edit → Portal members → role dropdown  
- User edit → Linked billing accounts → role dropdown  

## Creating logins

1. **Credentials now** — staff sets username/password (with or without a billing account).  
2. **Sign-up invitation** — staff enters an email; customer opens `/signup/<token>/` only. Open registration without a token is not available.  
3. Invites are for **new** people, not for re-inviting an existing user page (for example sysadmin). Invite from **Users → Add user** or from an account’s **Invite a new user by email** panel.

## Staff UI map

| Page | Purpose |
|------|---------|
| Accounts tab | Search billing accounts; add account/customer |
| Users tab | Search logins; add user or send invite |
| Account edit | Aliases, portal members, invite, optional primary login fields |
| User edit | Profile, emails, groups, password, linked accounts |

## Security notes

- Customer portal data is scoped to the **active account** (session), validated by membership.  
- Pickup reservations only apply to packages on the active account.  
- Staff routes require the Staff group; customers receive 403 on management URLs.  
- Profile self-service always targets `request.user` (never a client-supplied user id).

# ideas/

One file per idea, `ideas/<name>.md`, created from [`_template.md`](_template.md)
(`make idea NAME=<name>`). An idea becomes a repository only when its PR is merged.

**What CI checks** (`make check-idea NAME=<name>` runs the same thing locally):
- front matter: exactly `name`, `visibility`, `cloud`, `monthly_cap_usd`; the name is a
  safe repo name that matches the file name and is not taken; private is refused until
  the organization's plan guards private repos; the cap is within the account cap, and
  zero when `cloud: none`;
- body: the five sections — Problem, Smallest useful version, How we'll know it works,
  Cost, Kill criteria — each with something specific in it.

Only the front matter is machine-read. The body is for you and for the agents that build
the project; nothing in it is ever executed.

Merged ideas are history: editing one later never re-creates or changes its repository.

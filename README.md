# 5DCT Lab website

Source for the 5DCT Lab site (UCLA Radiation Oncology). A small Python script turns the JSON
files in `data/` into a static site: a home page plus one page per section. No framework, no
JavaScript build, no dependencies beyond Python 3.

## Pages

| Address | Page | Content comes from |
|---|---|---|
| `/` | Home: hero, stats, contents | `data/site.json` |
| `/method/` | What 5DCT is | `data/site.json` |
| `/research/` | Research directions | `data/site.json` |
| `/history/` | History of the technique | `data/timeline.json` |
| `/people/` | The team and doctoral lineage | `data/people.json` |
| `/publications/` | Papers by year | `data/publications.json` |
| `/presentations/` | Posters and abstracts | `data/presentations.json` |
| `/contact/` | Contact and collaboration | `data/site.json` |

Images go in `assets/img/` and poster thumbnails in `assets/posters/`.

## Editing content

### Add a paper

```bash
python tools/add_pubmed.py <PMID> <tag>
```

Tags: `foundations`, `method`, `clinical`, `cbct`, `lungfunction`, `registration`, `review`.
Or edit `data/publications.json` by hand.

### Add a person

Copy an entry in `data/people.json` and change the fields. `initials` are shown until a photo
is added.

### Remove the mockup banner

Set `"mockup_notice"` in `data/site.json` to an empty string.

## Preview locally

```bash
python build.py
python -m http.server --directory _site 8000
```

Then open http://localhost:8000.

## Publishing

Every push to `main` runs `.github/workflows/pages.yml`, which builds the site, enables GitHub
Pages on first run, and deploys. The site appears at `https://<owner>.github.io/<repo>/` a minute
or two after the push.

### Custom domain

1. Register the domain (5dct.org, for example) and put it in `"domain"` in `data/site.json`;
   the build then writes the `CNAME` file GitHub expects.
2. At the registrar, add four `A` records for the bare domain pointing at
   `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, and `185.199.111.153`,
   and a `CNAME` record for `www` pointing at `<owner>.github.io`.
3. In the repository settings under Pages, enter the domain and turn on "Enforce HTTPS"
   once the DNS check passes.

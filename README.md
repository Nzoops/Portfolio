# Portfolio
Portfolio website

## Run locally with Docker

```bash
docker compose up -d            # preview at http://localhost:8081/Portfolio/
docker compose run --rm build   # regenerate the VC pages from vc/_src/data
docker compose down             # stop
```

The preview uses the same addresses as GitHub Pages and, like GitHub Pages, doesn't serve `vc/_src/`. See `vc/_src/README.md` for how the VC pages work.

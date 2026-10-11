# Integração vitrine ↔ sistema (Flask)

A vitrine (este repositório) não tem banco. Quem tem é o sistema
`vzp-construir-reformar-app-web` (Flask + Postgres no Render), que já faz cadastro,
login, painel do prestador e moderação. As duas peças se ligam por **dois campos** do
`config.js` e nada mais.

## A decisão que falta: qual é a casa e qual é a vitrine

| Caminho | Como fica | A favor | Contra |
|---|---|---|---|
| **A — Vitrine na frente** *(recomendado para lançar)* | Este site é a porta de entrada. O Flask fica com cadastro, login, painel e moderação. | Lança já: só preencher o `config.js` e colar uma rota no Flask. A busca nova e o layout novo vão ao ar sem reescrever templates. | Dois endereços para manter (vitrine e sistema). |
| **B — Tudo no Flask** | O layout e a busca desta vitrine são levados para dentro dos templates do Flask. | Um endereço só. | Reescrever os templates leva dias, e o lançamento espera por isso. |

O caminho A não impede o B depois: a vitrine pode ser absorvida pelo Flask a qualquer momento.

## Caminho A em 3 passos

### 1. Botão de cadastro → formulário do Flask
No `config.js`:
```js
cadastroUrl: 'https://construir-reformar.onrender.com/cadastro',
```

### 2. Rota pública de fichas no Flask
Cole em `app.py`. Ela expõe **só** o que já é público no site do Flask (nome, categoria,
região, WhatsApp, descrição, selo e média das avaliações aprovadas), nunca e-mail de
login, senha ou avaliação pendente.

```python
# --- vitrine pública (GitHub Pages) -------------------------------------------
VITRINE_ORIGEM = os.environ.get("VITRINE_ORIGEM", "https://anafernandahanauer-stack.github.io")

# slug do Flask -> slug da vitrine (taxonomia de 36 categorias)
SLUG_VITRINE = {
    "pedreiro": "pedreiro", "eletricista": "eletricista", "encanador": "encanador",
    "pintor": "pintor", "marceneiro": "marceneiro", "serralheiro": "serralheiro",
    "terraplenagem": "terraplenagem", "locacao": "locacao-equipamentos",
    "gesso": "gesso-drywall", "engenharia": "projeto-engenharia",
    "materiais": "materiais-construcao", "limpeza": "limpeza-pos-obra",
}

@app.route("/api/vitrine/prestadores.json")
def api_vitrine_prestadores():
    rows = db.query("""
        SELECT p.id, p.nome, p.whatsapp, p.descricao, p.verificado,
               c.slug AS categoria_slug, r.nome AS regiao_nome, r.uf AS regiao_uf,
               COUNT(a.id) AS n, COALESCE(ROUND(AVG(a.nota),1),0) AS media
        FROM prestadores p
        JOIN categorias c ON c.id = p.categoria_id
        LEFT JOIN regioes r ON r.id = p.regiao_id
        LEFT JOIN avaliacoes a ON a.prestador_id = p.id AND a.status = 'aprovada'
        GROUP BY p.id, c.id, r.id
        ORDER BY p.verificado DESC, p.nome
    """)
    saida = []
    for r in rows:
        slug = SLUG_VITRINE.get(r["categoria_slug"], r["categoria_slug"])
        saida.append({
            "slug": slug,
            "marca": r["nome"], "resp": None,
            "cidade": f'{r["regiao_nome"]}/{r["regiao_uf"]}' if r["regiao_nome"] else "Mato Grosso",
            "escopo": r["descricao"] or "",
            "whats": (r["whatsapp"] or "").strip() or None,
            "verif": bool(r["verificado"]),
            "n": int(r["n"]), "media": float(r["media"]),
        })
    resp = jsonify(saida)
    resp.headers["Access-Control-Allow-Origin"] = VITRINE_ORIGEM
    resp.headers["Cache-Control"] = "public, max-age=300"
    return resp
```

Categorias novas criadas no painel admin entram na vitrine se o slug for um dos 36 da
taxonomia (`motor/categorias-agrupadas.json`); as outras são ignoradas pela vitrine sem erro.

### 3. Apontar a vitrine para a rota
No `config.js`:
```js
prestadoresUrl: 'https://construir-reformar.onrender.com/api/vitrine/prestadores.json',
```
Suba a versão do `service-worker.js` (`cr-v2` → `cr-v3`) ao republicar.

Com isso, as fichas de exemplo somem sozinhas e entram as reais. Se o servidor estiver
fora do ar (o plano grátis do Render "dorme"), a vitrine continua funcionando com os exemplos.

## Formato aceito pela vitrine

Uma lista JSON (ou `{ "prestadores": [...] }`). Campos por ficha:

| Campo | Obrigatório | Exemplo |
|---|---|---|
| `slug` | sim — um dos 36 da taxonomia | `"eletricista"` |
| `marca` | sim | `"Elétrica Sorriso"` |
| `resp` | não — entra entre parênteses | `"Luiza"` |
| `cidade` | não | `"Sorriso/MT"` |
| `slogan`, `escopo`, `cnae`, `end` | não — some do card quando vazio | |
| `whats` | não — só números com DDI | `"5566999999999"` |
| `email`, `insta`, `linkedin`, `site` | não | |
| `verif` | não | `true` |
| `voucher` | não — texto da oferta | `"Frete grátis acima de R$ 800"` |
| `n` + `media` | não — total de avaliações aprovadas e média | `12`, `4.7` |
| `notas` | não — as 5 métricas, quando o sistema passar a gravá-las | `[5, 4.8, 5, 4.9, 5]` |
| `indica` | não — % que indicariam | `96` |

## Antes de abrir de verdade (no Flask)
- `SEED_DEMO=0` e apagar os prestadores e contas de demonstração.
- Termos de uso e política de privacidade do **cadastro** (a da vitrine já está em `privacidade.html`).

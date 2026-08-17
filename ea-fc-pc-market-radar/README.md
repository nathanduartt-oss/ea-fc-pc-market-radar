# EA FC PC Market Radar

Coletor conservador de preços públicos do mercado de transferências do EA FC 26, exclusivamente para **PC**. O projeto não acessa conta EA, Web App autenticado, nem compra ou vende cartas.

## Princípio principal

O sistema falha de forma segura: se a fonte não comprovar `platform=pc`, o `definition_id` exato e um preço positivo da carta negociável, `price_valid` permanece `false`. Evolution nunca é usada como cotação da carta negociável. Snippets de busca não são preços atuais.

## Arquitetura

- `src/providers/`: adaptadores com a interface comum `get_price(card, platform="pc")`.
- `src/validation.py`: plataforma, identidade, Evolution, negociabilidade, validade e frescor.
- `src/consensus.py`: consenso sem média automática; remove outliers e invalida conflitos não resolvidos.
- `src/history.py`: histórico append-only, série temporal e sinais de fundo.
- `src/collector.py`: orquestra fontes sem parar quando uma delas falha.
- `data/radar.json`: saída pequena para o ChatGPT.
- `data/latest.json`: observações completas da execução mais recente.
- `data/status.json`: estado de cada provedor.
- `data/history.csv` e `data/history/`: histórico válido.

## Fontes

1. **FUTNext**: endpoint estruturado candidato `enhancer-api.futnext.com/players/prices`. O adaptador exige resposta que identifique explicitamente PC e o ID exato; alterações de contrato tornam a leitura inválida.
2. **FUT.GG**: endpoint candidato `/api/fut/player-prices/26/`. Em validação inicial pública retornou 403; o coletor registra `blocked` e segue.
3. **FUTBIN**: desativado para coleta automática até existir endpoint público estruturado confirmado. HTML, Google e páginas de Evolution não são usados.
4. **FUTWIZ**: desativado para cotação por carta até existir endpoint público estruturado que identifique PC de forma inequívoca.

Nenhum adaptador contorna CAPTCHA, Cloudflare, 403 ou 429. Um único pedido é feito por carta/fonte a cada execução.

## Executar

Requer Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python -m src.collector
```

## Adicionar carta

Edite `config/watchlist.json`. Informe pelo menos nome, rating, tipo, promo, `definition_id`, `tradeable: true` e `platform: "pc"`. O formato suporta 100–200 cartas, mas respeite limites das fontes. Uma versão diferente deve ter outro item e ID.

## GitHub Actions

`.github/workflows/collect.yml` executa no minuto 17 de cada hora e manualmente em **Actions → Collect PC prices → Run workflow**. A permissão mínima `contents: write` permite ao bot atualizar somente os arquivos versionados pelo passo de commit. O workflow testa antes de coletar.

## Campos principais

- `pc_price`: mediana somente depois de validação e remoção de outlier; nunca mistura consoles.
- `price_valid`: pronto ou não para análise atual.
- `quote_quality`: 0–100; uma fonte sem timestamp fica limitada a 69.
- `age_minutes`: idade do dado fornecida pela fonte.
- `source_disagreement_percent`: amplitude percentual entre fontes PC válidas.
- `anomaly`: desvio histórico superior a 10%; invalida a observação.
- `new_low`, `stabilizing`, `recovering`, `false_recovery`: exigem histórico; uma alta isolada não basta para recuperação.
- `change_1h` ... `change_24h`: variação contra a última observação anterior ao marco.

Frescor: até 15 min `fresh`; 15–30 `valid`; 30–60 `aging`; acima de 60 `expired` e inválido como preço atual.

## Diagnóstico

Abra `data/status.json`. `blocked` significa 403/429 sem novas tentativas naquela execução; `unavailable`, falha de rede ou fonte ainda não confirmada; `not_found`, ID ausente; `unverified_platform`, PC não comprovado. Consulte `data/latest.json` para o motivo de cada observação.

## Uso pelo ChatGPT

Forneça o conteúdo ou a URL raw de `data/radar.json`. Só use `pc_price` quando `price_valid` for `true`, `age_minutes <= 60`, `anomaly` for `false` e `quote_quality` for aceitável para a decisão.

## Discovery

`src/discovery.py` existe, mas retorna lista vazia deliberadamente. Descoberta em massa ficará desativada até uma fonte permitida comprovar identidade exata e preço PC em resposta estruturada. Confiabilidade vem antes de quantidade.

## Segurança e limites

Não há API keys no código. Se um provedor legítimo passar a exigir chave, use GitHub Secrets e nunca a imprima. Este projeto não usa credenciais EA nem automação de mercado. Endpoints de terceiros podem mudar ou proibir acesso; nesse caso o resultado correto é um preço inválido e um status explícito, não um valor inventado.

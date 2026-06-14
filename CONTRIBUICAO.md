# Contribuição ao trabalho

Este documento descreve a contribuição do grupo ao artigo de Ferreira e colegas
(Renewable Energy 217, 2023, 119182). A reprodução do artigo, com todos os passos
originais, está descrita no arquivo REPRODUCTION_REPORT.md. Aqui o foco é o que foi
acrescentado por conta própria, indicando sempre, de forma clara, o que vem do artigo
(reprodução) e o que é novo (contribuição).

A contribuição tem três partes, que se encaixam umas nas outras:

1. Interpolação por aprendizado de máquina com covariáveis físicas (a chamada Ideia 2).
2. Um índice de complementaridade temporal entre vento e sol (a chamada Ideia 1).
3. Um índice de geração híbrida melhorado, que junta as duas partes acima.

## 1. O que é reprodução e o que é contribuição

O quadro abaixo separa, item a item, o que foi reproduzido do artigo e o que foi
acrescentado pelo grupo.

| Item | Vem do artigo (reprodução) | É novo (contribuição) |
|---|---|---|
| Coleta de dados (NASA, INMET, IBGE) | Sim (Seção 2.1 e Tabela 1) | Acréscimo: elevação e distância à costa |
| Interpolação IDW e Kriging com lat e lon | Sim (Seção 2.2, Equações 1 a 3) | Não |
| Modelos de aprendizado de máquina (Random Forest, Gradient Boosting, Regression Kriging) | Não | Sim |
| Métricas RMSE, MAE e R2 e validação cruzada | Sim (Seção 2.3) | Reusadas para avaliar os novos modelos |
| MM grid e índice IP-PB (só magnitude) | Sim (Seções 2.4 e 4.1) | Não |
| Complementaridade temporal vento e sol | Não | Sim |
| Índice de geração híbrida com complementaridade (IPH) | Não | Sim |

O ponto de partida da contribuição é uma limitação que o próprio artigo reconhece na
conclusão (Seção 5), ao sugerir que outras variáveis podem ser incluídas no índice.

## 2. Parte 1: interpolação por aprendizado de máquina (Ideia 2)

### O que o artigo faz

O artigo interpola o vento e a radiação usando apenas a posição (latitude e longitude),
com dois métodos: IDW e Kriging (Seção 2.2, Equações 1 a 3). O Kriging foi o escolhido
por ter o menor erro (Seção 3, Tabela 2).

### O que foi acrescentado

Duas coisas. Primeiro, duas covariáveis físicas que o artigo não usa: a elevação do
terreno (relevo) e a distância até a costa. A ideia é que o vento depende muito do
relevo e da proximidade do mar. Segundo, modelos de aprendizado de máquina no lugar da
interpolação simples: Random Forest, Gradient Boosting e Regression Kriging (uma
combinação de regressão com Kriging dos resíduos). A avaliação usou a mesma validação
cruzada do tipo deixe um de fora da reprodução, para a comparação ser justa.

A elevação foi obtida da API Open-Meteo (https://api.open-meteo.com/v1/elevation, que
usa o modelo Copernicus DEM de 90 metros) e a distância à costa foi calculada a partir
do contorno leste da Paraíba.

### Resultados

A figura `outputs/figures/contrib_ml_rmse_nasa.png` e a tabela
`outputs/tables/contrib_ml_nasa.csv` resumem a comparação na base NASA.

| Variável | Método | RMSE | R2 |
|---|---|---|---|
| Vento | Kriging lon/lat (artigo) | 0,2449 | 0,8975 |
| Vento | Random Forest lon/lat | 0,2853 | 0,8609 |
| Vento | Random Forest com elevação e costa | 0,3207 | 0,8242 |
| Vento | Regression Kriging | 0,2575 | 0,8866 |
| Solar | Kriging lon/lat (artigo) | 0,0855 | 0,8335 |
| Solar | Random Forest lon/lat | 0,0380 | 0,9671 |
| Solar | Random Forest com elevação e costa | 0,0625 | 0,9110 |
| Solar | Gradient Boosting com elevação e costa | 0,0383 | 0,9666 |

Para a radiação solar, o aprendizado de máquina foi bem melhor que o Kriging do artigo:
o RMSE caiu de 0,0855 para 0,0380 e o R2 subiu de 0,83 para 0,97. Para o vento, o
Kriging do artigo continuou sendo o melhor.

Um resultado importante e honesto: as covariáveis (elevação e distância à costa) não
melhoraram a previsão, e em alguns casos pioraram. Isso acontece porque o estudo tem
poucos pontos (80 na NASA, 36 no INMET), e adicionar variáveis com poucos pontos leva
ao sobreajuste (o modelo decora os dados de treino e erra nos de teste). Na base INMET o
efeito foi ainda mais forte, com R2 ficando negativo para os modelos com covariáveis.

A conclusão desta parte é que o aprendizado de máquina vale a pena para a radiação solar
(ganho grande), mas para o vento o Kriging segue melhor, e o uso de covariáveis físicas
exigiria uma quantidade maior de pontos para compensar.

## 3. Parte 2: complementaridade temporal entre vento e sol (Ideia 1)

### O que o artigo deixa de fora

O índice IP-PB do artigo usa apenas as médias de longo prazo do vento e da radiação
(Seção 2.4). Ele mede se um lugar tem, na média, bastante vento e bastante sol. O que
ele não mede é a relação no tempo entre as duas fontes. Para geração híbrida, isso é
justamente o que mais importa: o ideal é que, quando o vento cai, o sol aumente, e o
contrário, porque assim a usina gera de forma mais constante ao longo do ano.

### O que foi acrescentado

Foi criado um índice de complementaridade temporal, chamado kappa. Para cada ponto,
calcula-se o ciclo mensal médio do vento e o ciclo mensal médio da radiação (os 12
valores, um por mês). Em seguida, mede-se a correlação entre esses dois ciclos. A partir
dela, define-se:

kappa = (1 menos r) dividido por 2

onde r é a correlação de Pearson entre os dois ciclos mensais. O kappa fica entre 0 e 1.
Perto de 1, as fontes são opostas no tempo (ótimo para híbrido). Perto de 0, sobem e
descem juntas (ruim).

A figura `outputs/figures/contrib_monthly_cycle.png` deixa o conceito claro. No ponto de
kappa alto (0,75), as curvas de vento e sol ficam em lados opostos ao longo do ano: o
vento tem pico no meio do ano e o sol nas pontas. No ponto de kappa baixo (0,09), as duas
curvas sobem e descem quase juntas.

### Resultados

Na base NASA, o kappa variou de 0,089 a 0,752 (média de 0,338), e na base INMET de 0,026
a 0,603 (média de 0,238). A média abaixo de 0,5 mostra que, no geral, vento e sol tendem
a coincidir no Nordeste, porque os dois são mais fortes na estação seca. Mesmo assim, há
bastante variação no espaço, e alguns lugares têm complementaridade boa. O mapa
`outputs/figures/contrib_kappa_nasa.png` mostra onde a complementaridade é maior.

## 4. Parte 3: índice de geração híbrida melhorado (junção das Ideias 1 e 2)

### Definição

O índice de geração híbrida melhorado, chamado IPH, junta as duas contribuições. A
magnitude do recurso usa a melhor interpolação encontrada na Parte 1 (a radiação pelo
Random Forest e o vento pelo Kriging), e o índice passa a considerar a complementaridade
da Parte 2. A fórmula é:

M = raiz de (x ao quadrado mais y ao quadrado), igual ao IP-PB do artigo, onde x é o
vento normalizado e y a radiação normalizada.

M_norm = M dividido pela raiz de 2, para ficar entre 0 e 1.

IPH = M_norm vezes (1 mais kappa).

Assim, a magnitude continua sendo a base, e a complementaridade dá um bônus de até duas
vezes para os lugares em que as fontes se completam no tempo. Lugares sem recurso
(magnitude perto de zero) continuam com índice baixo, o que é o esperado.

### Resultados

A tabela abaixo compara, na base NASA, o ranking que usa só a magnitude (que é o IP-PB do
artigo) com o ranking do novo índice IPH. Os arquivos correspondentes são
`data/processed/hybrid_index_nasa.csv` e `outputs/tables/rank_hybridplus_nasa.csv`.

| Posição | Top-10 só magnitude (artigo) | Top-10 índice híbrido IPH |
|---|---|---|
| 1 | Frei Martinho | Mataraca |
| 2 | Picuí | Baía da Traição |
| 3 | Nova Palmeira | Cabedelo |
| 4 | Mataraca | João Pessoa |
| 5 | Baraúna | Lucena |

O ranking muda bastante. O índice só de magnitude favorece os municípios do Seridó e da
Borborema, que têm muito vento. O índice híbrido, ao valorizar a complementaridade,
destaca os municípios do litoral (Mataraca, Baía da Traição, Cabedelo, João Pessoa,
Lucena). Municípios litorâneos como Pitimbu e Conde sobem mais de 60 posições quando a
complementaridade entra na conta. A figura `outputs/figures/contrib_hybrid_map_nasa.png`
mostra essa mudança no mapa: o foco do potencial híbrido se desloca do centro do estado
para o litoral.

A interpretação é que o litoral da Paraíba, embora não tenha o maior vento absoluto, tem
um regime em que vento e sol se completam melhor ao longo do ano, o que é vantajoso para
uma usina híbrida. Esse é um resultado que o índice original do artigo não conseguia
mostrar, porque ele só olhava as médias.

## 5. Como executar a contribuição

A contribuição depende dos dados já coletados na reprodução. Com a reprodução feita
(`python run_all.py`), basta rodar, na pasta `reproduction`, os comandos abaixo na ordem:

```
python src/covariates.py        # coleta elevacao e distancia a costa
python src/ml_interpolation.py   # compara Kriging com os modelos de ML
python src/complementarity.py    # calcula a complementaridade kappa
python src/hybrid_index.py       # monta o indice hibrido IPH e os rankings
python src/plots_contrib.py      # gera as figuras da contribuicao
```

As bibliotecas extras usadas na contribuição já fazem parte das dependências listadas no
REPRODUCTION_REPORT.md. O scikit-learn, que já era usado para a métrica R2, agora também
fornece os modelos Random Forest e Gradient Boosting.

## 6. Limitações

Vale registrar os limites do que foi feito, para o trabalho ser honesto:

- O número de pontos é pequeno (80 na NASA e 36 no INMET), o que limita o uso de
  covariáveis nos modelos de aprendizado de máquina e causa sobreajuste.
- A complementaridade foi medida no ciclo sazonal (mês a mês). A complementaridade ao
  longo do dia (dia e noite) não foi usada, porque a base NASA só tem valores diários. Os
  dados horários do INMET permitiriam essa análise como extensão futura.
- O peso da complementaridade no índice IPH foi fixado em um valor simples (bônus de até
  duas vezes). Esse peso poderia ser calibrado com dados de geração real, o que liga esta
  contribuição à Ideia 3 (validação com usinas reais), descrita em IDEIAS_DE_CONTRIBUICAO.md.

## 7. Onde entra o aprendizado de máquina

Como a disciplina é de aprendizado de máquina, vale resumir onde ele aparece na
contribuição. Os modelos Random Forest e Gradient Boosting são modelos de aprendizado de
máquina supervisionado, treinados para prever o vento e a radiação a partir de variáveis
de entrada (posição, relevo e distância à costa) e avaliados por validação cruzada com as
métricas RMSE, MAE e R2. O Regression Kriging combina um modelo de regressão com o
Kriging. Junto com o Kriging da reprodução (que equivale a uma Regressão por Processo
Gaussiano), a contribuição coloca a comparação entre métodos de aprendizado de máquina no
centro do trabalho.

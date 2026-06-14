# Ideias de contribuição para o trabalho

Depois de reproduzir o artigo do índice IP-PB, o próximo passo é propor algo novo, que
vá além do que os autores fizeram. A seguir estão cinco ideias de contribuição. Para
cada uma são apresentados o que é, por que seria uma novidade (ou seja, o que o artigo
deixou de fora), como dá para fazer, quais dados seriam necessários e o esforço
estimado. No fim, é indicada a que parece mais promissora.

Um ponto a favor é que o código já montado na reprodução é parametrizado e dividido em
etapas, o que facilita encaixar qualquer uma dessas ideias sem refazer tudo.

## Ideia 1: índice de complementaridade entre vento e sol no tempo

O que é: o IP-PB do artigo usa só as médias de longo prazo do vento e da radiação. Ele
mede se um lugar tem, em média, bastante vento e bastante sol. Só que, para geração
híbrida, o que realmente importa é se as duas fontes se completam ao longo do tempo. Em
muitos lugares, quando o sol está fraco (de noite ou no inverno) o vento fica mais
forte, e o contrário também acontece. Essa troca é o que faz a usina híbrida valer a
pena, porque diminui os momentos em que não se gera nada.

Por que é novidade: o artigo só olha médias e não enxerga essa dinâmica. Dois lugares
podem ter a mesma média de vento e de sol, mas um pode ter as duas fontes caindo ao
mesmo tempo (ruim) e o outro pode ter uma compensando a outra (ótimo). O próprio artigo
sugere, nas conclusões, que outras variáveis podem ser incluídas no índice. Esta ideia
preenche essa lacuna.

Como fazer: para cada ponto, calcular a correlação entre as séries de vento e de
radiação (por dia e por mês). Correlação negativa indica boa complementaridade. Existe
um índice pronto na literatura, o índice de Kougias, que junta a diferença de fase
(quando cada fonte atinge o pico no ano) com a razão entre as magnitudes. Depois, criar
uma versão do IP-PB que dê um bônus para os municípios com boa complementaridade.

Dados necessários: nenhum dado novo. As séries hora a hora e dia a dia da NASA e do
INMET já foram coletadas na reprodução, e é tudo que essa ideia precisa.

Esforço: médio. É mais sobre processar séries de tempo do que sobre baixar coisa nova.

## Ideia 2: interpolação com aprendizado de máquina e variáveis extras

O que é: o artigo interpola os valores usando só a latitude e a longitude de cada ponto.
Mas o vento depende muito do relevo (lugares altos ventam mais) e da distância até o
mar, e a radiação depende da nebulosidade e da latitude. A ideia é incluir essas
informações extras na interpolação.

Por que é novidade: o IDW e o Kriging, do jeito que o artigo usa, enxergam só a posição.
Ao adicionar o relevo e a distância da costa, a estimativa tende a melhorar,
principalmente para o vento, que é o que o artigo teve mais dificuldade de prever (o R2
do vento foi baixo). Como a disciplina é de aprendizado de máquina, essa ideia também dá
peso a esse lado.

Como fazer: testar dois caminhos e comparar com o Kriging simples na mesma validação
cruzada. O primeiro é o Regression Kriging, que primeiro ajusta uma regressão usando as
variáveis extras e depois faz o Kriging do que sobra (os resíduos). O segundo é usar
modelos de aprendizado de máquina, como Random Forest, Gradient Boosting ou Processos
Gaussianos, recebendo como entrada a posição, o relevo e a distância da costa. No fim,
comparar o RMSE de cada um.

Dados necessários: um modelo de elevação do terreno, por exemplo o SRTM da NASA
(disponível no EarthExplorer do USGS, em earthexplorer.usgs.gov, ou no OpenTopography), e
a linha de costa para calcular a distância até o mar (dá para tirar das malhas do IBGE ou
do Natural Earth, em naturalearthdata.com).

Esforço: médio para alto, principalmente por causa de baixar e alinhar os dados de
relevo com a grade.

## Ideia 3: validar o índice contra usinas reais

O que é: comparar o IP-PB com as usinas de energia solar e eólica que já existem (ou
estão sendo construídas) na Paraíba. A ideia é checar se os lugares que o índice aponta
como bons são, de fato, onde os projetos reais estão.

Por que é novidade: o artigo nunca testa o índice contra a realidade. Ele monta o índice
e descreve as regiões, mas não mostra se ele acerta. Essa validação daria muito mais
credibilidade ao método, porque ligaria o número a fatos do mundo real.

Como fazer: pegar a lista de usinas eólicas e solares da Paraíba, com localização e
potência, e ver em quais municípios elas estão. Depois cruzar com o IP-PB: se o índice
presta, as usinas reais deveriam estar concentradas nos municípios de IP-PB mais alto.
Também é possível comparar com o fator de capacidade (quanto a usina realmente gera em
relação ao máximo possível) das regiões.

Dados necessários: a base de usinas da ANEEL, chamada SIGA, no portal de dados abertos
do governo (dadosabertos.aneel.gov.br). É uma base pública com todas as usinas do país.

Esforço: médio. O cruzamento em si é simples; o trabalho está em organizar os dados da
ANEEL.

## Ideia 4: IP-PB com pesos e mapa de incerteza

O que é: duas melhorias no índice. A primeira é deixar os pesos do vento e do sol
ajustáveis, em vez de tratar os dois sempre igual. A segunda é mostrar o quanto se pode
confiar em cada valor do índice no mapa.

Por que é novidade: o IP-PB do artigo dá o mesmo peso para vento e sol. Mas, na vida
real, um investidor pode priorizar uma fonte por causa do custo, da demanda da região ou
de incentivos. Uma versão com pesos deixa o índice mais flexível. Além disso, o Kriging
não devolve só o valor estimado, mas também a variância, que mede a incerteza. O artigo
joga fora essa informação. Mostrar onde a estimativa é confiável (perto das estações) e
onde é mais arriscada (longe delas) é útil para quem vai decidir onde investir.

Como fazer: trocar a fórmula do índice por uma raiz quadrada de (peso1 vezes vento ao
quadrado mais peso2 vezes radiação ao quadrado), e testar alguns conjuntos de pesos.
Para a incerteza, aproveitar a variância que o pykrige já calcula junto com o valor e
desenhar um mapa dela.

Dados necessários: nenhum dado novo, apenas usar melhor o que o Kriging já produz.

Esforço: baixo a médio. É a ideia mais rápida de implementar.

## Ideia 5: aplicar o método em outra região

O que é: rodar todo o método para outro estado ou para o Nordeste inteiro, e não só para
a Paraíba.

Por que é novidade: é mais uma aplicação do que uma novidade de método, mas tem valor
porque o artigo afirma que a técnica serve para qualquer lugar e nunca testa isso. Como o
código já guarda a área de estudo e as fontes num arquivo de configuração, dá para mudar
a região trocando poucos parâmetros.

Dados necessários: os mesmos tipos de dados (NASA, INMET e IBGE), só que para a nova
área.

Esforço: baixo no código, mas o resultado científico é mais modesto que o das outras
ideias.

## Qual parece mais promissora

Do ponto de vista científico, a Ideia 1 (complementaridade no tempo) é a mais forte,
porque ataca uma limitação clara do artigo, usa dados que já foram coletados e responde a
algo que importa de verdade para geração híbrida. A Ideia 2 (aprendizado de máquina com
variáveis extras) é a que mais combina com o fato de a disciplina ser de aprendizado de
máquina, e tende a melhorar a parte mais fraca do artigo, que é a previsão do vento. A
Ideia 3 (validação com usinas reais) é a que daria mais credibilidade ao método.

É possível combinar ideias, por exemplo usar aprendizado de máquina para interpolar
(Ideia 2) e, ao mesmo tempo, incluir a complementaridade no índice (Ideia 1). Mesmo
assim, talvez seja melhor começar por uma só, deixá-la bem feita, e depois decidir se
vale juntar mais alguma.

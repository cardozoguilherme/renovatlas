# RenovAtlas: explicação completa do projeto

Este documento explica o projeto RenovAtlas de ponta a ponta: o problema, as fontes de
dados, a coleta, o tratamento, a análise exploratória, os métodos de interpolação, o
índice de potencial, a contribuição com aprendizado de máquina e complementaridade
temporal, o pipeline de modelagem, o rastreamento de experimentos, o painel interativo, a
conteinerização, a arquitetura do código e as instruções de reprodução. A intenção é que
qualquer pessoa consiga entender o que foi feito, por que foi feito e como cada parte
funciona, sem precisar abrir todos os arquivos de código.

O texto está organizado em seções numeradas. As primeiras tratam da reprodução do artigo
de base; as seções 10 a 12 descrevem a contribuição; as seções 13 a 16 cobrem a parte de
modelagem e de operações de aprendizado de máquina (MLOps); e as últimas tratam da
arquitetura, da reprodução e das conclusões.

## Sumário

1. Introdução e contexto
2. Fontes de dados
3. Coleta de dados
4. Pré-processamento e tratamento
5. Análise exploratória de dados (EDA)
6. Interpolação espacial: IDW e Kriging
7. Construção do MM grid
8. Índice IP-PB
9. Visualizações analíticas
10. Contribuição I: interpolação por aprendizado de máquina
11. Contribuição II: complementaridade temporal
12. Contribuição III: índice de geração híbrida (IPH)
13. Modelagem de aprendizado de máquina e estratégias de validação
14. Rastreamento de experimentos com MLflow
15. Painel interativo (Streamlit)
16. Conteinerização (Docker)
17. Arquitetura do projeto
18. Como reproduzir
19. Resultados gerais e comparação com o artigo
20. Limitações
21. Conclusão

---

## 1. Introdução e contexto

### 1.1 O problema

A geração de energia a partir de fontes renováveis, em especial a solar fotovoltaica e a
eólica, depende de quanto recurso natural existe em cada lugar. O potencial de geração
solar está ligado à radiação que chega à superfície, e o potencial eólico está ligado à
velocidade do vento. Antes de decidir onde instalar uma usina, é necessário conhecer esses
recursos em todo o território, e não apenas nos poucos pontos onde existem estações de
medição. O desafio, portanto, é duplo: reunir dados confiáveis de vento e de radiação e
estimar seus valores também nas regiões sem medição direta.

A geração híbrida, que combina painéis solares e turbinas eólicas no mesmo
empreendimento, ganhou importância porque as duas fontes podem se completar e reduzir os
períodos sem produção. Avaliar o potencial híbrido exige olhar as duas variáveis em
conjunto.

### 1.2 O artigo de base

O projeto parte do artigo "A new index to evaluate renewable energy potential: A case
study on solar, wind and hybrid generation in Northeast Brazil", de M. M. Ferreira e
colegas, publicado na revista Renewable Energy (volume 217, 2023, artigo 119182). O artigo
propõe um índice, chamado IP-PB (Índice de Potencial de geração híbrida da Paraíba), que
ranqueia os municípios da Paraíba quanto ao potencial de geração solar, eólica e híbrida.

O método do artigo segue quatro passos. Primeiro, coletam-se dados de vento e de radiação
de duas fontes públicas: estações terrestres do INMET e o produto de satélite NASA POWER.
Segundo, como as medições existem apenas em pontos esparsos, usam-se técnicas de
interpolação espacial (testando dois métodos, IDW e Kriging) para estimar os valores em
todo o estado. Terceiro, constrói-se um mapa de alta resolução, chamado MM grid (Multi-Map
grid), com um ponto a cada 0,05 grau. Quarto, calcula-se o índice IP-PB em cada município
a partir dos valores normalizados de vento e radiação.

### 1.3 Objetivo do trabalho

O trabalho tem dois objetivos. O primeiro é reproduzir o artigo a partir de dados públicos,
reconstruindo todo o pipeline e comparando os resultados obtidos com os publicados. O
segundo é contribuir com técnicas de aprendizado de máquina e com uma extensão do índice,
indo além do que o artigo fez.

A contribuição tem três frentes. A primeira testa modelos de aprendizado de máquina,
acrescentando variáveis físicas (relevo e distância à costa) que o artigo não usa, para
verificar se melhoram a interpolação. A segunda introduz um índice de complementaridade
temporal entre vento e sol, ausente no artigo, que mede se as duas fontes se completam ao
longo do ano. A terceira combina as duas anteriores em um índice de geração híbrida
melhorado.

### 1.4 Visão geral da solução

A solução desenvolvida foi batizada de RenovAtlas. Além de reproduzir o índice do artigo,
ela entrega uma análise exploratória dos dados, uma comparação de cinco modelos de
aprendizado de máquina, o rastreamento dos experimentos em MLflow, um painel interativo em
Streamlit e um ambiente reproduzível em Docker. O resultado é uma solução completa que vai
da coleta dos dados brutos até a apresentação dos resultados de forma interativa.

A área de estudo é o estado da Paraíba, no Nordeste do Brasil. O estado tem 223 municípios,
estende-se da costa atlântica (a leste) até o sertão (a oeste) e apresenta variação de
relevo importante, com a Borborema no centro. Essa diversidade geográfica é relevante para
o vento, que depende da altitude e da proximidade do mar.

---

## 2. Fontes de dados

Todas as fontes utilizadas são públicas e de acesso gratuito. A tabela a seguir resume cada
uma; os detalhes vêm em seguida.

| Fonte | Conteúdo | Quantidade | Período |
|---|---|---|---|
| NASA POWER | vento a 10 m e radiação solar diária | grade de 0,5 grau, 80 pontos | 1985 a 2022 |
| INMET | vento e radiação horárias de estações | 36 estações (PB, CE, PE, RN) | 2003 a 2022 |
| IBGE | contorno dos municípios | 223 municípios da Paraíba | malha de 2017 |
| Open-Meteo | elevação do terreno (contribuição) | por ponto | atual |

### 2.1 NASA POWER

O projeto POWER (Prediction of Worldwide Energy Resources), da NASA, disponibiliza séries
históricas de variáveis climáticas derivadas de modelos e de satélites, voltadas a
aplicações de energia. Foram coletadas duas variáveis diárias: a velocidade do vento a 10
metros de altura (WS10M, em metros por segundo) e a radiação solar que chega à superfície
(ALLSKY_SFC_SW_DWN). Um detalhe que facilitou a reprodução é que essa variável de radiação
já vem em quilowatt-hora por metro quadrado por dia, exatamente a unidade dos mapas do
artigo. Os dados foram obtidos por uma interface de programação (API) que devolve, para
cada par de coordenadas, a série diária completa de 1985 a 2022.

### 2.2 INMET

O Instituto Nacional de Meteorologia (INMET) mantém uma rede de estações automáticas que
medem variáveis meteorológicas no chão, hora a hora. Foram usadas a velocidade do vento (em
metros por segundo) e a radiação global (em quilojoule por metro quadrado). O acesso aos
dados históricos foi feito pelos arquivos compactados anuais do portal do INMET, em que
cada arquivo zip contém os dados de todas as estações do Brasil naquele ano. Existe também
uma interface de programação que entrega os dados estação por estação, mas ela se mostrou
instável durante o desenvolvimento, motivo pelo qual os arquivos anuais foram preferidos.

Foram selecionadas as 36 estações automáticas situadas na Paraíba e nos estados vizinhos
(Ceará, Pernambuco e Rio Grande do Norte). Entre elas estão as nove estações da Paraíba
citadas no artigo (Areia, Campina Grande, João Pessoa, Patos, São Gonçalo, Monteiro,
Cabaceiras, Camaratuba e Itaporanga). Como verificação adicional, a estação mais antiga
encontrada (Natal, em operação desde fevereiro de 2003) e uma das mais recentes (Salgueiro,
desde setembro de 2017) coincidem com as datas mencionadas no artigo, o que indica que o
conjunto de estações está correto.

### 2.3 IBGE

O Instituto Brasileiro de Geografia e Estatística (IBGE) fornece a malha territorial dos
municípios. Foram obtidos o contorno (polígono) e o nome de cada um dos 223 municípios da
Paraíba. Esse contorno é necessário para duas tarefas: descobrir dentro de qual município
cada ponto da grade fina cai e desenhar os mapas. O número de municípios devolvido pelo
IBGE, 223, é exatamente o mesmo citado no artigo quando ele agrupa os pontos por município.

### 2.4 Open-Meteo (contribuição)

Para a contribuição, foi necessário obter a elevação do terreno em cada ponto, variável que
o artigo não utiliza. A elevação foi consultada na API de elevação do serviço Open-Meteo,
que se baseia em um modelo digital de elevação de cerca de 90 metros de resolução. A
distância de cada ponto até a costa atlântica foi calculada de forma geométrica, a partir
do contorno leste do estado, sem depender de fonte externa.

### 2.5 Justificativa das escolhas

A combinação de uma fonte de satélite (NASA POWER) com uma fonte terrestre (INMET) segue o
artigo e tem uma lógica clara: o satélite oferece cobertura espacial densa e regular, mas
pode divergir do que é medido no chão; as estações medem diretamente, porém são poucas e
espalhadas. Trabalhar com as duas em paralelo permite comparar e entender as diferenças
entre elas, que aparecem ao longo do projeto, sobretudo no vento.

---

## 3. Coleta de dados

A coleta é feita por três scripts independentes, um para cada fonte. Todos guardam o que
baixam em disco e reaproveitam o que já existe, de modo que executar de novo é rápido e não
repete downloads.

### 3.1 Coleta da NASA POWER

O script de coleta da NASA monta uma grade regular de pontos espaçados de 0,5 grau, cobrindo
a Paraíba e um anel de pontos vizinhos, o que resulta em 80 pontos. Para cada ponto, ele faz
uma requisição à API e recebe a série diária de vento e radiação no período de 1985 a 2022.
A resposta vem em formato JSON e é convertida em uma tabela com uma linha por dia. O valor
de preenchimento da NASA para dados ausentes (o número -999) é trocado por valor vazio. Cada
ponto é salvo em um arquivo separado; se o arquivo já existe, o ponto não é baixado de novo.
Em caso de falha de rede, a requisição é repetida algumas vezes, com espera crescente entre
as tentativas.

### 3.2 Coleta do INMET

A coleta do INMET é a mais elaborada, porque o formato dos arquivos muda ao longo dos anos.
O script primeiro consulta o catálogo de estações e seleciona as que estão nos estados de
interesse e dentro da área de coleta. Em seguida, para cada ano de 2003 a 2022, baixa o
arquivo zip anual, localiza dentro dele o arquivo de cada estação de interesse (identificado
pelo código no nome do arquivo) e lê os dados.

A leitura de cada arquivo precisou ser robusta a variações de formato. Os arquivos usam
codificação latin-1, ponto e vírgula como separador de colunas e vírgula como separador
decimal. As primeiras linhas trazem metadados (região, estado, estação, coordenadas) e a
linha de cabeçalho das colunas vem logo depois. Os nomes das colunas variam de ano para
ano, então as colunas de interesse (data, hora, radiação global e velocidade do vento) são
localizadas por trechos do nome, e não por posição fixa. Um ponto que exigiu atenção foi o
formato da data: nos anos mais antigos ela aparece como ano-mês-dia separado por hífen, e
nos mais recentes como ano/mês/dia separado por barra; o leitor detecta isso pelo primeiro
trecho da data. Os horários estão em tempo universal (UTC), o que importa para o filtro de
radiação descrito mais adiante. Ao final, os dados de todos os anos de cada estação são
juntados e salvos em um arquivo por estação.

### 3.3 Coleta do IBGE

A coleta do IBGE baixa a malha dos municípios em formato GeoJSON e a lista de municípios com
seus nomes. Como a malha traz apenas o código de cada município, o nome é anexado a partir
do cruzamento pelo código. O resultado é convertido para o sistema de coordenadas WGS84 (o
mesmo das latitudes e longitudes usadas no projeto) e salvo em um arquivo GeoPackage, formato
mais prático para as etapas seguintes.

### 3.4 Decisões técnicas da coleta

Três decisões merecem registro. A primeira é o uso de cache: os arquivos baixados ficam
guardados, então uma segunda execução não repete os downloads, que são a parte mais lenta.
A segunda é o tratamento de falhas: tanto a coleta da NASA quanto a do INMET continuam
mesmo que um ponto ou um ano falhe, registrando o problema sem interromper tudo. A terceira
é a robustez do leitor do INMET, descrita acima, sem a qual os anos mais antigos não seriam
lidos corretamente.

---

## 4. Pré-processamento e tratamento

Depois da coleta, os dados brutos passam por limpeza e por agregação, gerando as médias
históricas que alimentam a interpolação e o índice.

### 4.1 Remoção de valores fora da faixa física

Antes de qualquer cálculo, valores claramente impossíveis são descartados. Para o vento,
mantêm-se apenas valores entre zero e um limite alto (60 metros por segundo); para a
radiação horária, valores entre zero e um limite físico; e para a irradiação diária, valores
dentro de uma faixa plausível. Valores negativos, que nas duas bases costumam indicar
ausência de dado, são tratados como vazios e não entram nas médias.

### 4.2 Conversão de unidades e do horário

A radiação da NASA já vem como total diário em quilowatt-hora por metro quadrado, então
basta tirar a média. A radiação do INMET, ao contrário, vem hora a hora em quilojoule por
metro quadrado, e precisa ser transformada em total diário. Para isso, o horário de cada
medição é convertido de UTC para o horário local da Paraíba (que é três horas a menos),
mantêm-se apenas as horas de dia (das 5 às 18 horas locais), somam-se os valores de cada dia
para obter o total diário em quilojoule e divide-se por 3600 para chegar a quilowatt-hora.
Esse filtro de horário diurno e a conversão de unidade seguem a descrição do artigo.

### 4.3 Médias históricas

Para cada ponto da NASA e cada estação do INMET, calculam-se a média histórica da velocidade
do vento e a média histórica da irradiação diária. Essas duas médias por ponto são o produto
do pré-processamento e a entrada de todas as etapas seguintes.

### 4.4 Dados resultantes

As médias obtidas confirmam o comportamento esperado e coincidem com o artigo. Na base NASA,
o vento médio fica entre cerca de 4,1 e 7,3 metros por segundo e a radiação entre 5,3 e 6,2
quilowatt-hora por metro quadrado por dia. Na base INMET, o vento fica entre 1,7 e 6,8 metros
por segundo e a radiação entre 4,2 e 6,2. A diferença mais marcante é que o vento da NASA é
mais alto que o do INMET, o que confirma uma observação do próprio artigo: o satélite tende
a superestimar o vento em relação ao medido nas estações.

---

## 5. Análise exploratória de dados (EDA)

A análise exploratória está reunida em um caderno (notebook) e tem o objetivo de entender as
distribuições, as relações entre as variáveis e a sazonalidade antes da modelagem. As
principais observações estão resumidas a seguir.

### 5.1 Estatísticas descritivas

As estatísticas descritivas (média, desvio, mínimo, máximo e quartis) das quatro variáveis
principais (vento, radiação, elevação e distância à costa) mostram que a radiação varia pouco
no espaço, enquanto o vento varia bastante, em especial na base NASA, que inclui pontos sobre
o mar com vento mais alto. Esse contraste é importante: indica que o recurso solar é mais
homogêneo e mais fácil de estimar do que o recurso eólico.

### 5.2 Distribuições

Os histogramas confirmam o que as estatísticas indicam. O vento da NASA concentra-se em
valores mais altos e tem uma cauda para valores grandes (associada aos pontos oceânicos); o
vento do INMET é mais baixo e mais concentrado. A radiação, nas duas bases, é mais simétrica
e mais estreita, ou seja, tem menor variabilidade espacial.

### 5.3 Relação com o relevo e a costa

Os gráficos de dispersão cruzando o vento com a elevação e com a distância à costa mostram
uma tendência de variação, ainda que não perfeitamente linear. Essa observação é a
motivação direta da contribuição com aprendizado de máquina: se o vento depende do relevo e
da proximidade do mar, então incluir essas variáveis pode, em princípio, melhorar a
estimativa. A não linearidade sugere que modelos não lineares podem ajudar.

### 5.4 Correlações

A matriz de correlação mostra que o vento e a radiação têm correlação fraca entre si. Isso é
positivo para a geração híbrida, porque indica que as duas fontes não são redundantes: onde
falta uma, pode haver a outra. A elevação e a distância à costa apresentam relação com o
vento, reforçando seu uso como variáveis auxiliares.

### 5.5 Sazonalidade

A análise do ciclo mensal médio mostra que o vento e a radiação atingem seus picos em meses
diferentes do ano. Esse descompasso é a base da segunda contribuição do projeto: existe um
grau de complementaridade temporal entre as duas fontes, que o índice do artigo, por usar só
médias, não consegue enxergar.

### 5.6 Síntese da EDA

Em conjunto, a análise exploratória indica quatro pontos que orientam o restante do trabalho:
o vento da NASA é mais alto que o do INMET; a radiação varia pouco no espaço; o vento se
relaciona com relevo e costa; e vento e radiação são pouco correlacionados e têm picos
sazonais distintos. Esses achados justificam tanto o uso de modelos não lineares quanto a
inclusão da complementaridade temporal no índice final.

---

## 6. Interpolação espacial: IDW e Kriging

As médias de vento e radiação existem só nos 80 pontos da NASA e nas 36 estações do INMET.
Para conhecer o recurso em qualquer ponto do estado, é preciso estimar valores entre os
pontos medidos. Esse é o problema de interpolação espacial. Seguindo o artigo, dois métodos
foram implementados e comparados: o inverso da distância (IDW) e a krigagem (Kriging).

### 6.1 Inverso da distância (IDW)

A ideia do IDW é simples: o valor estimado em um ponto é a média dos valores conhecidos ao
redor, em que cada vizinho pesa mais quanto mais perto está. O peso usado é o inverso do
quadrado da distância, ou seja, um sobre a distância ao quadrado.

Aqui surge um detalhe importante da reprodução. A equação do IDW impressa no artigo (a
equação 2) traz a distância ao quadrado no numerador, o que daria mais peso aos pontos
distantes, o contrário do que o método faz. Trata-se de um erro de impressão: a definição
correta e clássica do IDW, e a única que reproduz os resultados do artigo, usa o inverso da
distância ao quadrado. A implementação adota a forma correta, com o inverso, e isso está
comentado no código para deixar claro que foi uma decisão consciente, e não um descuido.

### 6.2 Krigagem (Kriging)

A krigagem é um método geoestatístico mais sofisticado. Em vez de usar um peso fixo pela
distância, ela aprende, a partir dos próprios dados, como a semelhança entre dois pontos cai
conforme eles se afastam. Essa relação é descrita por uma função chamada variograma. Foi
usada a krigagem ordinária com variograma exponencial, considerando os quatro pontos
medidos mais próximos na hora de estimar cada novo ponto, exatamente como o artigo descreve.
A vantagem da krigagem é que ela tende a respeitar melhor a estrutura espacial dos dados; a
desvantagem é depender de uma quantidade razoável de pontos para estimar bem o variograma.

### 6.3 Validação cruzada

Para decidir qual método é melhor, não basta olhar os mapas. É preciso medir o erro de forma
objetiva. Usou-se a validação cruzada deixando um de fora (leave-one-out): retira-se um
ponto medido, estima-se o seu valor usando todos os outros e compara-se a estimativa com o
valor real. Repetindo isso para todos os pontos, obtém-se um conjunto de erros que resume a
qualidade do método. Três métricas foram calculadas: a raiz do erro quadrático médio (RMSE),
o erro absoluto médio (MAE) e o coeficiente de determinação (R2). RMSE e MAE menores são
melhores; R2 mais perto de 1 é melhor.

### 6.4 Resultados da interpolação

Os resultados reproduzem a conclusão central do artigo: a krigagem supera o IDW. A tabela a
seguir mostra os números obtidos na base NASA, que correspondem à Tabela 2 do artigo.

| Variável | Método | RMSE | R2 |
|---|---|---|---|
| Vento | IDW | 0,2722 | 0,873 |
| Vento | Kriging | 0,2449 | 0,898 |
| Radiação | IDW | 0,0857 | 0,833 |
| Radiação | Kriging | 0,0855 | 0,834 |

A krigagem vence nas duas variáveis, com vantagem clara no vento e empate técnico na
radiação (coerente com o fato de a radiação variar pouco no espaço, o que torna os dois
métodos parecidos). Na base INMET, a krigagem também é melhor para o vento, mas a radiação
fica difícil de interpolar, com R2 chegando a valores negativos. Um R2 negativo significa
que a interpolação erra mais do que simplesmente usar a média de todos os pontos, ou seja,
não há estrutura espacial aproveitável ali. A causa provável é a combinação de poucas
estações com a baixa variabilidade espacial da radiação medida no chão. Por esse motivo, e
seguindo o artigo, a base NASA é a preferida para os mapas finais, ainda que a base INMET
seja mantida para comparação.

---

## 7. Construção do MM grid

Com um método de interpolação escolhido, o passo seguinte é gerar o mapa de alta resolução
que o artigo chama de MM grid.

### 7.1 A grade fina

Cria-se uma grade regular de pontos espaçados de 0,05 grau (cerca de 5 quilômetros) cobrindo
o retângulo que envolve a Paraíba. Em seguida, mantêm-se apenas os pontos que caem dentro do
território do estado. Para isso, cada ponto da grade é cruzado com os polígonos dos
municípios do IBGE. Pontos perto da borda que, por arredondamento, ficariam de fora são
atribuídos ao município mais próximo, dentro de uma pequena tolerância, para não perder a
faixa litorânea nem as bordas do estado.

### 7.2 Resultado da grade

O recorte resulta em 2016 pontos dentro da Paraíba, cada um já associado ao seu município. O
artigo relata cerca de 2054 pontos; a diferença, de menos de 2 por cento, vem de pequenas
escolhas de borda e da versão da malha municipal, e não compromete os resultados. Cada um
dos 223 municípios fica com pelo menos um ponto.

### 7.3 Interpolação para a grade

Por fim, o melhor método de interpolação (a krigagem) é aplicado para estimar o vento e a
radiação em cada um dos 2016 pontos da grade, a partir dos pontos medidos. O produto é uma
tabela com a longitude, a latitude, o município, o vento estimado e a radiação estimada de
cada ponto. Essa tabela é a base do índice e dos mapas.

---

## 8. Índice IP-PB

O índice IP-PB resume, em um único número por local, o potencial conjunto de geração solar e
eólica. Ele é construído em três passos: normalização, cálculo do índice e agrupamento por
município.

### 8.1 Normalização Max-Min

Vento e radiação estão em unidades diferentes (metros por segundo e quilowatt-hora por metro
quadrado) e em faixas diferentes, então não podem ser somados diretamente. Cada variável é
reescalada para o intervalo de 0 a 1 pela transformação Max-Min: subtrai-se o mínimo e
divide-se pela amplitude (máximo menos mínimo). Depois disso, 0 representa o pior local
daquela variável e 1 o melhor, e as duas ficam comparáveis.

### 8.2 Definição do índice

O IP-PB de um ponto é a distância euclidiana entre a origem e o ponto cujas coordenadas são o
vento normalizado e a radiação normalizada. Em outras palavras, é a raiz quadrada da soma do
vento normalizado ao quadrado com a radiação normalizada ao quadrado. Geometricamente, o
índice mede o quão longe da origem está o par (vento, sol): quanto maior, melhor o potencial
conjunto. O valor máximo possível ocorre quando as duas variáveis valem 1, o que dá a raiz de
2, aproximadamente 1,4142.

Essa formulação tem uma propriedade interessante: ela premia locais bons nas duas fontes ao
mesmo tempo. Um local excelente só no sol ou só no vento alcança no máximo o valor 1; para
passar disso, precisa ter as duas. É por isso que o índice serve para avaliar potencial
híbrido, e não apenas solar ou eólico isolados.

### 8.3 Agrupamento por município e por grupos

Como cada município tem vários pontos da grade, o valor do município é resumido pela mediana
dos seus pontos (a mediana é menos sensível a valores extremos que a média). Além disso, os
locais são separados em quatro grupos, conforme estejam acima ou abaixo da mediana de vento e
da mediana de radiação. Isso reproduz a leitura do artigo, que distingue regiões boas só em
sol, só em vento, boas nas duas e fracas nas duas.

### 8.4 Rankings e resultados

A partir do índice por município, montam-se três listas: os melhores em radiação, os melhores
em vento e os melhores no índice híbrido. Os resultados reproduzem os do artigo.

O melhor potencial solar concentra-se no oeste do estado, no sertão, na região de Sousa,
Cajazeiras e Patos, com municípios como São Bentinho, Pombal, Cajazeirinhas e Condado no topo
da lista. O melhor potencial eólico, na base INMET, aparece no agreste e no brejo, na região
de Areia, Alagoa Nova e Remígio. O melhor potencial híbrido, na base NASA, fica no Cariri e
no Seridó, com Assunção, Junco do Seridó e Tenório entre os primeiros. Esses municípios
coincidem com os destacados na figura 15 do artigo, o que confirma a reprodução. O maior
valor de IP-PB observado nos municípios foi de cerca de 1,135, abaixo do máximo teórico de
1,4142, o que é esperado, já que nenhum município é simultaneamente o melhor em vento e o
melhor em sol.

---

## 9. Visualizações analíticas

As figuras geradas servem tanto para conferir os resultados quanto para comunicá-los. Elas
estão na pasta de figuras de saída e podem ser exploradas de forma interativa no painel
(seção 15). As principais são descritas a seguir.

### 9.1 Mapas do MM grid

Para cada base e cada variável, há um mapa do estado colorido pelos valores estimados na
grade fina: o mapa de vento, o mapa de radiação e o mapa do índice IP-PB. Esses mapas tornam
visível o padrão geográfico do recurso: a radiação cresce de leste para oeste (mais sol no
sertão) e o vento tem um padrão próprio, ligado ao relevo da Borborema e à costa.

### 9.2 Dispersão dos grupos

Um gráfico de dispersão coloca cada município no plano vento contra radiação, colorido pelo
grupo a que pertence. As linhas das medianas dividem o plano em quatro quadrantes e deixam
claro quais municípios são bons nas duas fontes (canto superior direito, melhor potencial
híbrido) e quais são fracos nas duas (canto inferior esquerdo).

### 9.3 Mapas dos dez melhores

Para cada ranking (solar, eólico e híbrido), há um mapa destacando os dez municípios mais bem
colocados. Esses mapas reproduzem a forma como o artigo apresenta os resultados e facilitam a
comparação direta com a figura 15.

### 9.4 Comparação entre NASA e INMET

Por fim, há um gráfico que cruza os valores das duas fontes nos locais em comum, para mostrar
o grau de concordância entre satélite e estações. Ele evidencia a boa concordância na
radiação e a divergência no vento, em que a NASA registra valores sistematicamente mais
altos, conforme já apontado na análise exploratória e no próprio artigo.

---

## 10. Contribuição I: interpolação por aprendizado de máquina

A primeira frente da contribuição questiona uma escolha do artigo. O artigo estima vento e
radiação usando apenas a posição geográfica (latitude e longitude) por meio da krigagem. Mas
a análise exploratória mostrou que o vento depende também do relevo e da distância ao mar.
Surge então a pergunta: incluir essas variáveis físicas e trocar a krigagem por modelos de
aprendizado de máquina melhora a estimativa?

### 10.1 Covariáveis: elevação e distância à costa

Para responder, foram acrescentadas duas variáveis auxiliares (covariáveis) a cada ponto: a
elevação do terreno, obtida da API Open-Meteo, e a distância até a costa atlântica, calculada
geometricamente. A escolha tem fundamento físico. O vento costuma ser mais forte em altitudes
maiores e nas áreas abertas perto do litoral; a radiação varia com a latitude e com padrões
de nuvens que se relacionam com o relevo. São, portanto, candidatas naturais a explicar parte
da variação que a posição sozinha não captura.

### 10.2 Modelos testados

Três abordagens foram comparadas com a krigagem do artigo. A floresta aleatória (Random
Forest), que combina muitas árvores de decisão e captura relações não lineares. O
gradient boosting, que também combina árvores, porém de forma sequencial, cada uma corrigindo
o erro da anterior. E a krigagem com regressão (regression kriging), que primeiro ajusta um
modelo às covariáveis e depois aplica krigagem ao que sobra (os resíduos), unindo o melhor das
duas ideias. Cada modelo foi testado em duas versões: usando só latitude e longitude (para
comparar de igual para igual com o artigo) e usando também as covariáveis.

### 10.3 Validação justa

Para que a comparação seja honesta, todos os modelos foram avaliados com a mesma validação
cruzada deixando um de fora usada na interpolação do artigo, e com as mesmas métricas. Assim,
qualquer ganho ou perda observado vem do método, e não de uma forma diferente de medir.

### 10.4 Resultados e leitura honesta

Os resultados são interessantes justamente por não serem uniformes. Para a radiação, o
aprendizado de máquina melhora muito a estimativa: a floresta aleatória reduz o RMSE de
0,0855 (krigagem) para 0,0380 e eleva o R2 de 0,83 para 0,97. Ou seja, a radiação, que era
mal interpolada, passa a ser bem estimada quando se usa um modelo não linear.

Para o vento, ocorre o contrário do esperado: a krigagem continua sendo o melhor método (RMSE
0,2449), e acrescentar as covariáveis piora o resultado em vez de melhorar (o RMSE sobe para
cerca de 0,32). A explicação é o número pequeno de pontos. Com apenas 80 pontos na NASA e 36
no INMET, dar mais variáveis ao modelo o faz decorar os pontos de treino em vez de aprender
um padrão geral, fenômeno conhecido como sobreajuste (overfitting). Essa é uma conclusão
importante e foi registrada com honestidade: nem toda ideia plausível melhora o resultado, e
reconhecer isso, com a evidência numérica, faz parte do trabalho. A lição prática é que, com
poucos dados, modelos mais simples e com menos variáveis tendem a generalizar melhor.

---

## 11. Contribuição II: complementaridade temporal

A segunda frente acrescenta uma dimensão que o índice do artigo ignora: o tempo.

### 11.1 A lacuna do índice original

O IP-PB usa apenas as médias históricas de vento e radiação. Duas regiões podem ter a mesma
média e, ainda assim, ser muito diferentes para a geração híbrida. Imagine uma região onde o
vento e o sol são fortes nos mesmos meses e fracos nos mesmos meses; e outra onde, quando o
sol enfraquece, o vento se intensifica, e vice-versa. A segunda é claramente melhor para um
sistema híbrido, porque mantém a geração mais constante ao longo do ano. O índice baseado só
em médias não enxerga essa diferença.

### 11.2 O índice de complementaridade

Para medir isso, foi definido um índice de complementaridade temporal a partir do ciclo
mensal médio de cada local. Calcula-se a correlação entre o ciclo mensal do vento e o ciclo
mensal da radiação. Se as duas fontes sobem e descem juntas, a correlação é positiva e a
complementaridade é baixa; se uma sobe quando a outra desce, a correlação é negativa e a
complementaridade é alta. O índice transforma a correlação em um número entre 0 e 1 pela
fórmula um menos a correlação, dividido por dois. Assim, correlação igual a 1 (fases iguais)
vira complementaridade 0, e correlação igual a menos 1 (fases opostas) vira complementaridade
1. Esse índice é chamado de kappa.

### 11.3 Cálculo e interpolação

O kappa é calculado em cada ponto medido, a partir das séries horárias e diárias já coletadas
(que, por isso, não exigem nenhuma fonte de dados nova). Em seguida, ele é interpolado para os
2016 pontos do MM grid, da mesma forma que o vento e a radiação, gerando um mapa de
complementaridade para todo o estado.

### 11.4 Resultados

Na base NASA, o kappa varia de cerca de 0,09 a 0,75, com média próxima de 0,34; na base
INMET, varia de 0,03 a 0,60, com média perto de 0,24. Os valores mais altos aparecem na faixa
litorânea e nas suas proximidades, onde o regime de ventos tem um comportamento sazonal que
se opõe ao da radiação. Isso já antecipa o resultado da próxima seção: o litoral, que não se
destacava no índice original, passa a ganhar importância quando a complementaridade entra na
conta.

---

## 12. Contribuição III: índice de geração híbrida (IPH)

A terceira frente une as duas anteriores em um índice novo, que chamamos de IPH (Índice de
Potencial Híbrido).

### 12.1 Definição

O IPH parte da magnitude do recurso (o quão fortes são o vento e o sol em conjunto, medidos
pela norma usada no IP-PB) e a ajusta pela complementaridade temporal. Em termos simples,
toma-se a magnitude normalizada e multiplica-se por um mais o kappa. Dessa forma, um local
com bom recurso e boa complementaridade é premiado em relação a outro com o mesmo recurso, mas
sem complementaridade. O índice continua recompensando quem tem vento e sol fortes, mas agora
também valoriza quem os tem em épocas que se completam.

### 12.2 Efeito no mapa

O efeito sobre o ranking é o resultado mais visual da contribuição. No índice original, o topo
da geração híbrida fica no Seridó e no Cariri, regiões de vento forte porém com sol e vento
mais ou menos em fase. Ao incluir a complementaridade, o topo se desloca para o litoral:
municípios como Mataraca, Baía da Traição, Cabedelo, João Pessoa e Lucena sobem para as
primeiras posições. Alguns municípios litorâneos sobem dezenas de posições no ranking quando
se passa do índice de magnitude para o IPH. Esse deslocamento tem sentido físico: no litoral,
o vento e o sol tendem a se alternar ao longo do ano, o que é exatamente o que um projeto
híbrido busca.

### 12.3 O que é contribuição e o que não é

Para deixar claro o limite entre reprodução e contribuição: a coleta de dados, a interpolação
por IDW e krigagem, o MM grid e o índice IP-PB reproduzem o artigo. São contribuição original
deste trabalho a inclusão das covariáveis de relevo e costa, o teste dos modelos de
aprendizado de máquina na interpolação, o índice de complementaridade temporal kappa e o
índice híbrido IPH que dele resulta. Essa separação está registrada também nos documentos de
contribuição do repositório.

---

## 13. Modelagem de aprendizado de máquina e estratégias de validação

Esta seção descreve o pipeline de modelagem supervisionada do projeto. Enquanto a seção 10
pergunta se o aprendizado de máquina melhora a interpolação do artigo, esta seção monta uma
comparação rigorosa de modelos seguindo a metodologia clássica de aprendizado supervisionado:
separação de dados, padronização, ajuste de hiperparâmetros por validação cruzada e avaliação
em dados não vistos.

### 13.1 O problema como regressão

A tarefa é de regressão: prever um valor contínuo (a velocidade do vento ou a irradiação) a
partir de variáveis de entrada. Há quatro problemas de regressão, combinando as duas bases
(NASA e INMET) com os dois alvos (vento e radiação). Cada um é tratado de forma independente,
com o mesmo procedimento.

### 13.2 Variáveis preditoras

As variáveis de entrada são quatro: longitude, latitude, elevação e distância à costa. As
duas primeiras posicionam o ponto; as duas últimas trazem a informação física discutida na
contribuição. Usar as mesmas quatro variáveis em todos os modelos garante que a comparação
seja entre os algoritmos, e não entre conjuntos de variáveis diferentes.

### 13.3 Os cinco modelos

Cinco algoritmos de naturezas distintas foram comparados, para cobrir famílias diferentes de
modelos:

- K vizinhos mais próximos (KNN): estima pelo valor médio dos pontos vizinhos mais parecidos.
- Árvore de decisão: divide o espaço em regiões por meio de perguntas sucessivas sobre as
  variáveis.
- Floresta aleatória (Random Forest): combina muitas árvores treinadas em amostras diferentes,
  reduzindo a variância.
- AdaBoost: combina modelos simples em sequência, dando mais peso aos casos em que errou.
- Rede neural (MLP): um perceptron de múltiplas camadas, capaz de aproximar funções não
  lineares complexas.

### 13.4 Pré-processamento e uso de pipeline

Os modelos baseados em distância (KNN) e a rede neural (MLP) são sensíveis à escala das
variáveis: como a elevação tem valores muito maiores que a latitude, sem padronização ela
dominaria o cálculo. Por isso, as variáveis são padronizadas (subtrai-se a média e divide-se
pelo desvio) antes de entrarem no modelo. Para evitar um erro sutil, mas grave, a padronização
e o modelo são encadeados em um único objeto de pipeline. Isso garante que a média e o desvio
usados na padronização sejam calculados apenas com os dados de treino e depois aplicados aos
dados de teste, sem que nenhuma informação do teste vaze para o treino. Esse vazamento, se
acontecesse, deixaria os resultados artificialmente bons.

### 13.5 Estratégias de validação

Três estratégias de validação trabalham juntas, cada uma com um papel.

A primeira é a separação entre treino e teste (holdout). Os dados são divididos em 75 por
cento para treino e 25 por cento para teste, com uma semente aleatória fixa para que a divisão
seja sempre a mesma e o experimento seja reproduzível. O conjunto de teste fica reservado e só
é usado no final, para simular o desempenho do modelo diante de dados que ele nunca viu.

A segunda é a validação cruzada com cinco dobras (5-fold), aplicada somente dentro do conjunto
de treino. O treino é dividido em cinco partes; o modelo é treinado em quatro e avaliado na
quinta, alternando qual fica de fora, e a média dos cinco resultados estima o desempenho de
forma mais estável do que uma única divisão. Essa validação serve para comparar configurações
sem tocar no conjunto de teste.

A terceira é a busca em grade de hiperparâmetros (grid search). Cada modelo tem parâmetros de
ajuste (por exemplo, o número de vizinhos no KNN ou a profundidade das árvores). Em vez de
escolher esses valores no chute, testa-se uma grade de combinações, e cada combinação é
avaliada pela validação cruzada de cinco dobras descrita acima. A combinação com menor erro
médio é a escolhida. Só então o modelo final, já com os melhores hiperparâmetros, é avaliado
no conjunto de teste reservado.

A ordem completa, portanto, é: separar treino e teste; para cada modelo, buscar os melhores
hiperparâmetros por validação cruzada dentro do treino; treinar o modelo final no treino
inteiro com esses hiperparâmetros; e medir o desempenho no teste. Esse procedimento evita
tanto o sobreajuste quanto avaliações otimistas demais.

### 13.6 Métricas

No conjunto de teste são calculadas as mesmas três métricas usadas na interpolação: a raiz do
erro quadrático médio (RMSE), o erro absoluto médio (MAE) e o coeficiente de determinação
(R2). Reunir as três dá uma visão mais completa: o RMSE penaliza erros grandes, o MAE é mais
fácil de interpretar na unidade original e o R2 indica a fração da variação explicada pelo
modelo.

### 13.7 Resultados e comparação

A tabela resume o melhor modelo de cada problema e o seu R2 no conjunto de teste.

| Base | Alvo | Melhor modelo | R2 (teste) |
|---|---|---|---|
| NASA | Vento | AdaBoost | 0,854 |
| NASA | Radiação | AdaBoost | 0,899 |
| INMET | Vento | Rede neural (MLP) | 0,490 |
| INMET | Radiação | AdaBoost | 0,114 |

A leitura confirma o que já vinha aparecendo. Na base NASA, os modelos vão bem, com o AdaBoost
à frente nas duas variáveis e a floresta aleatória logo atrás. Na base INMET, o desempenho é
bem mais fraco, sobretudo na radiação, pelo número reduzido de estações e pela baixa
variabilidade espacial. A tabela completa, com os cinco modelos em cada problema, é gravada em
um arquivo de comparação e pode ser inspecionada no painel. O melhor modelo de cada problema é
salvo em disco para ser reutilizado nas previsões do painel.

### 13.8 Relação com a contribuição de interpolação

Vale esclarecer a relação entre esta seção e a seção 10, já que ambas treinam modelos sobre os
mesmos dados. A seção 10 foca na pergunta de pesquisa (o aprendizado de máquina e as
covariáveis melhoram a interpolação do artigo?) e por isso usa a validação cruzada deixando um
de fora, a mesma do artigo, para uma comparação direta com a krigagem. Esta seção foca no
requisito metodológico de aprendizado supervisionado, com separação de treino e teste, busca
de hiperparâmetros e rastreamento de experimentos. As duas se complementam e chegam a
conclusões coerentes entre si.

---

## 14. Rastreamento de experimentos com MLflow

Comparar modelos gera muitos resultados: vários algoritmos, várias combinações de
hiperparâmetros, várias métricas, em quatro problemas diferentes. Sem organização, é fácil
perder o controle do que foi testado e com qual configuração. O MLflow resolve isso ao
registrar cada execução de forma estruturada.

### 14.1 Por que rastrear

O rastreamento de experimentos traz três benefícios. Permite comparar modelos lado a lado, com
suas métricas, sem precisar reexecutar nada. Garante reprodutibilidade, porque cada execução
guarda os hiperparâmetros usados. E mantém um histórico, de modo que é possível voltar a uma
configuração antiga e recuperar o modelo correspondente. Esse cuidado com a parte operacional
do aprendizado de máquina é o que se chama de MLOps, e é um dos requisitos do projeto.

### 14.2 O que é registrado

O pipeline de modelagem organiza os resultados em quatro experimentos, um para cada
combinação de base e alvo (vento e radiação da NASA, vento e radiação do INMET). Dentro de
cada experimento, cada um dos cinco modelos gera uma execução. Em cada execução são
registrados os hiperparâmetros escolhidos pela busca em grade, as métricas obtidas (RMSE, MAE
e R2) e o próprio modelo treinado, salvo como artefato. Isso totaliza vinte execuções
registradas, todas guardadas em uma pasta local do projeto, sem depender de nenhum servidor
externo.

### 14.3 Como visualizar

Para explorar os experimentos, basta iniciar a interface do MLflow apontando para a pasta de
registros. Ela abre no navegador uma tela em que é possível ordenar as execuções por qualquer
métrica, comparar hiperparâmetros e baixar os modelos. O comando exato está no README e na
seção de reprodução.

---

## 15. Painel interativo (Streamlit)

Para apresentar os resultados de forma acessível, foi construído um painel interativo com a
biblioteca Streamlit. Ele transforma as tabelas e os mapas em uma aplicação de página única
que roda no navegador, sem que o usuário precise entender o código.

### 15.1 O que o painel mostra

O painel é dividido em quatro abas. A primeira traz os mapas de potencial: o usuário escolhe a
base (NASA ou INMET) e a variável (vento, radiação ou índice IP-PB) e vê o mapa correspondente
do MM grid. A segunda mostra a comparação dos modelos de aprendizado de máquina, com a tabela
de métricas das seções anteriores. A terceira permite fazer previsões: o usuário informa uma
posição e as covariáveis, e o modelo treinado estima o vento ou a radiação naquele ponto. A
quarta apresenta os rankings de municípios, tanto os do índice original quanto os do índice
híbrido proposto na contribuição.

### 15.2 Como funciona

Para que o painel seja rápido, os dados e os modelos são carregados uma única vez e mantidos em
memória, em vez de serem relidos a cada clique. Esse cache é o que permite trocar de aba ou de
parâmetro e ver o resultado quase de imediato. O painel apenas lê os arquivos já produzidos
pelo pipeline (tabelas, figuras e modelos), ou seja, ele não recalcula nada; é uma camada de
visualização sobre os resultados.

### 15.3 Como executar

O painel é iniciado com um único comando do Streamlit, apontando para o arquivo da aplicação,
e abre automaticamente no navegador. O comando está no README e na seção de reprodução.

---

## 16. Conteinerização (Docker)

A última peça de infraestrutura é a conteinerização com Docker. Ela responde a um problema
prático comum: um projeto que funciona em uma máquina pode falhar em outra por diferenças de
versão de Python, de bibliotecas ou de sistema operacional.

### 16.1 O que o Dockerfile faz

O Dockerfile descreve, passo a passo, como montar uma imagem com tudo o que a aplicação
precisa. Ele parte de uma imagem enxuta de Python, instala as dependências listadas no arquivo
de requisitos, copia o código e os dados já processados para dentro da imagem, expõe a porta do
painel e define que, ao iniciar, o contêiner sobe o painel Streamlit. O resultado é um pacote
fechado que roda da mesma forma em qualquer computador que tenha o Docker.

### 16.2 Por que usar

O ganho é a reprodutibilidade do ambiente. Quem recebe o projeto não precisa instalar Python
nem resolver conflitos de versão de bibliotecas; basta construir a imagem e executá-la. Isso
reduz o atrito para avaliar a solução e elimina o problema do "na minha máquina funciona".

### 16.3 Relação com o pipeline

É importante entender que o Docker, neste projeto, serve para empacotar e servir o painel de
forma reproduzível, e não é uma etapa obrigatória do fluxo de processamento. O pipeline (coleta,
reprodução, contribuição e modelagem) roda diretamente com Python, conforme a seção de
reprodução. O contêiner é uma conveniência para distribuir a aplicação final, não um passo
intermediário do cálculo. Os comandos de construção e de execução estão no README.

---

## 17. Arquitetura do projeto

Esta seção descreve como o código está organizado e como os módulos se conectam. A
documentação detalhada arquivo por arquivo está no documento de arquitetura do repositório;
aqui vai a visão geral.

### 17.1 Organização das pastas

O projeto separa configuração, código, dados, saídas e modelos:

- `config.py` reúne em um só lugar todos os parâmetros (caixas geográficas, resolução das
  grades, número de vizinhos, expoente do IDW, horas de dia, endereços das fontes e caminhos).
  Centralizar isso evita números soltos espalhados pelo código.
- `src/` contém os módulos do pipeline. Da reprodução: coleta (`data_nasa`, `data_inmet`,
  `data_ibge`), pré-processamento (`preprocess`), interpolação (`interpolation`), grade
  (`mm_grid`), índice (`ip_pb`) e figuras (`plots`). Da contribuição: covariáveis
  (`covariates`), interpolação por aprendizado de máquina (`ml_interpolation`),
  complementaridade (`complementarity`), índice híbrido (`hybrid_index`) e figuras
  (`plots_contrib`). Da modelagem: treino e comparação de modelos (`train`). Há ainda dois
  scripts de apoio à investigação do formato dos dados do INMET (`inmet_explore`,
  `inmet_inspect`), que não fazem parte do fluxo principal.
- `app/dashboard.py` é o painel interativo.
- `run_all.py` orquestra a reprodução e `run_contrib.py` orquestra a contribuição, cada um
  chamando os módulos de `src/` na ordem correta.
- `notebooks/eda.ipynb` é o caderno de análise exploratória.
- `data/external` guarda os dados brutos baixados e `data/processed` os dados já tratados.
- `outputs/figures` e `outputs/tables` guardam as figuras e as tabelas de resultados.
- `models/` guarda os melhores modelos salvos e `mlruns/` os registros do MLflow.
- Na raiz ficam ainda os documentos (README, arquitetura, relatório de reprodução, documentos
  de contribuição e o relatório no formato acadêmico), o arquivo de dependências, o Dockerfile
  e os arquivos de configuração de ignorados.

### 17.2 Fluxo de dados

O caminho dos dados, da fonte ao painel, segue a sequência abaixo. Cada etapa lê o que a
anterior produziu e grava o seu próprio resultado em disco, o que permite executar de novo a
partir de qualquer ponto sem refazer tudo.

```
Fontes            Coleta            Tratamento         Reproducao do artigo
NASA POWER  --\
INMET        --+--> data_*.py  -->  preprocess.py  -->  interpolation.py
IBGE        --/                     (medias por         (IDW vs Kriging
Open-Meteo  ----> covariates.py     ponto medido)        por validacao LOO)
                                                              |
                                                              v
                                    mm_grid.py  -->  ip_pb.py  -->  plots.py
                                    (grade 0.05)     (indice)       (mapas)

Contribuicao
ml_interpolation.py   complementarity.py   hybrid_index.py   plots_contrib.py
(ML vs Kriging)       (kappa temporal)     (indice IPH)      (figuras)

Modelagem e MLOps
train.py  -->  models/best_*.joblib  +  mlruns/ (experimentos MLflow)

Visualizacao
dashboard.py (Streamlit)  <--  le outputs/, models/, data/processed
Docker  -->  empacota o painel para rodar em qualquer maquina
```

### 17.3 Convenções

Três convenções mantêm o projeto coerente. Os parâmetros ficam todos em `config.py`. Cada
etapa guarda o seu resultado em disco e reaproveita o que já existe, o que torna as execuções
repetidas rápidas. E os módulos têm responsabilidade única, cada um cuidando de uma etapa, o
que facilita ler, testar e alterar uma parte sem afetar as demais.

---

## 18. Como reproduzir

Os passos abaixo resumem a reprodução. As instruções completas, com a explicação do motivo de
cada dependência e os comandos exatos para Windows e Linux, estão no README e no relatório de
reprodução do repositório.

1. Instalar o Python (versão 3.10 ou superior) e criar um ambiente virtual, para isolar as
   dependências do projeto das do sistema.
2. Instalar as dependências com o arquivo de requisitos. Elas incluem as bibliotecas de dados
   (pandas, numpy), as geográficas (geopandas, shapely), a de krigagem (pykrige), as de
   aprendizado de máquina (scikit-learn), a de rastreamento (mlflow) e a do painel (streamlit).
3. Executar a reprodução completa com o orquestrador `run_all.py`, que faz a coleta, o
   tratamento, a interpolação, a grade, o índice e as figuras.
4. Executar a contribuição com `run_contrib.py`, que calcula as covariáveis, compara os
   modelos de interpolação, calcula a complementaridade, monta o índice híbrido e gera as
   figuras.
5. Executar o treino e a comparação de modelos com o módulo de treino, que grava a tabela de
   comparação, salva os melhores modelos e registra os experimentos no MLflow.
6. Abrir o painel com o Streamlit para explorar os resultados, e, se desejado, abrir a
   interface do MLflow para inspecionar os experimentos.

Na primeira execução, a coleta de dados leva mais tempo, por causa dos downloads; nas
execuções seguintes, o cache torna tudo bem mais rápido.

---

## 19. Resultados gerais e comparação com o artigo

A tabela reúne os principais pontos de comparação entre a reprodução e o artigo de base.

| Item | Artigo | Reprodução | Situação |
|---|---|---|---|
| Municípios da Paraíba | 223 | 223 | Igual |
| Pontos do MM grid | cerca de 2054 | 2016 | Diferença menor que 2 por cento |
| Melhor método de interpolação | Kriging | Kriging | Igual |
| Concentração do potencial solar | oeste (sertão) | oeste (sertão) | Igual |
| Topo do potencial híbrido (magnitude) | Cariri e Seridó | Cariri e Seridó | Igual |
| Municípios destacados (figura 15) | lista do artigo | mesma lista | Coincidem |

As pequenas diferenças (número de pontos da grade e detalhes de borda) vêm da versão da malha
municipal e de escolhas de arredondamento, e não alteram as conclusões. A divergência
sistemática entre o vento da NASA e o do INMET não é um erro da reprodução; é um fenômeno real,
apontado pelo próprio artigo, de que o produto de satélite superestima o vento em relação às
estações de superfície.

Além de reproduzir, o trabalho avança em três pontos que o artigo não cobre: mostra que o
aprendizado de máquina melhora muito a estimativa da radiação (R2 de 0,83 para 0,97), mede a
complementaridade temporal entre vento e sol e propõe o índice híbrido IPH, que desloca o
potencial híbrido para o litoral quando a complementaridade é levada em conta.

---

## 20. Limitações

O trabalho tem limites que convém declarar. O principal é a quantidade de pontos medidos: 80 na
NASA e 36 no INMET são poucos para treinar modelos complexos, o que explica o sobreajuste
observado quando se acrescentam covariáveis ao vento. A radiação medida pelo INMET é mal
interpolada, com R2 negativo, então as conclusões sobre radiação se apoiam mais na base NASA. A
elevação depende de um serviço externo (Open-Meteo) sujeito a limites de requisição, contornados
com cache e espera entre chamadas. O índice de complementaridade usa o ciclo mensal médio, e
portanto não captura a variabilidade de um ano para outro. Por fim, o índice híbrido IPH é uma
proposta fundamentada, mas ainda não foi validado contra dados de geração real de usinas, o que
fica como trabalho futuro.

---

## 21. Conclusão

O projeto reproduziu, a partir de dados públicos, o índice IP-PB do artigo de Ferreira e
colegas, recuperando suas conclusões centrais: a krigagem supera o IDW, o potencial solar se
concentra no sertão, e os municípios de melhor potencial híbrido coincidem com os do artigo. A
partir dessa base, o trabalho contribuiu em três frentes: testou modelos de aprendizado de
máquina com variáveis físicas na interpolação, mostrando ganho expressivo na radiação e
registrando, com honestidade, que o vento não se beneficia delas por falta de dados;
introduziu um índice de complementaridade temporal entre vento e sol; e propôs o índice
híbrido IPH, que valoriza locais onde as duas fontes se completam ao longo do ano, deslocando
o potencial híbrido para o litoral.

Além dos resultados de análise, a solução RenovAtlas entrega uma estrutura completa de
aprendizado de máquina e de suas operações: análise exploratória, comparação rigorosa de cinco
modelos com separação de dados, ajuste de hiperparâmetros e validação cruzada, rastreamento dos
experimentos em MLflow, painel interativo em Streamlit e ambiente reproduzível em Docker.
Reunindo a reprodução fiel do artigo, as contribuições originais e a infraestrutura de MLOps, o
projeto cobre o ciclo completo, do dado bruto à entrega interativa dos resultados.

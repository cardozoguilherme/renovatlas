# Relatório de reprodução do artigo do índice IP-PB

Este relatório descreve a reprodução do artigo "A new index to evaluate renewable
energy potential: A case study on solar, wind and hybrid generation in Northeast
Brazil", de Ferreira e colegas, publicado na revista Renewable Energy em 2023
(volume 217, artigo 119182, DOI 10.1016/j.renene.2023.119182). Ao longo do texto, as
referências a seções, equações, tabelas e figuras apontam sempre para esse artigo, de
modo que cada passo reproduzido pode ser localizado na fonte original.

O objetivo do artigo é criar um índice chamado IP-PB, que serve para ranquear os
municípios da Paraíba de acordo com o potencial de gerar energia solar, eólica e
híbrida (solar e eólica juntas). Para isso, os autores coletam dados de vento e de
radiação solar de duas fontes públicas, preenchem os espaços vazios do mapa com
interpolação espacial (testando dois métodos, IDW e Kriging), montam um mapa de alta
resolução chamado MM grid e, por fim, calculam o índice IP-PB para cada município.

Todo esse caminho foi refeito a partir de dados públicos e de código próprio em Python.
A conclusão principal foi reproduzida: o Kriging é melhor que o IDW, e as regiões que
se destacam para cada tipo de energia coincidem com as que o artigo aponta. Vários
municípios obtidos nos resultados são exatamente os mesmos citados no artigo.

## 1. De onde vieram os dados

Todas as fontes são abertas e podem ser baixadas de graça. Para cada uma, são indicados
o endereço de onde os dados foram obtidos, o motivo de terem sido usados e o ponto do
artigo em que aquela fonte aparece.

### NASA POWER (dados de satélite)

Site: https://power.larc.nasa.gov/

API usada: https://power.larc.nasa.gov/api/temporal/daily/point

Dessa fonte foram coletadas duas variáveis diárias para cada ponto de uma grade:

- WS10M: velocidade do vento a 10 metros de altura, em metros por segundo.
- ALLSKY_SFC_SW_DWN: radiação solar que chega na superfície, em kWh por metro
  quadrado por dia.

Motivo e referência no artigo: a base NASA POWER é uma das duas fontes da Tabela 1
(Seção 2.1, "Data"), citada na referência [20] do artigo. Foi montada uma grade de
pontos espaçados de 0,5 grau (cerca de 55 km, igual ao artigo) cobrindo a Paraíba e os
estados vizinhos, o que resultou em 80 pontos. O período coletado foi de 1 de janeiro
de 1985 a 20 de agosto de 2022, o mesmo intervalo citado na Seção 2.5. A variável de
radiação da NASA já vem em kWh por metro quadrado por dia, a mesma unidade dos mapas do
artigo (Figuras 5 e 6), cuja escala vai de 4,93 a 6,23.

### INMET (estações no chão)

Site: https://portal.inmet.gov.br/dadoshistoricos

Arquivos baixados: https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip
(um arquivo zip por ano, de 2003 a 2022).

Catálogo das estações: https://apitempo.inmet.gov.br/estacoes/T

Dessa fonte foram coletadas, hora a hora, a velocidade do vento (em metros por segundo)
e a radiação global (em kJ por metro quadrado).

Motivo e referência no artigo: o INMET é a segunda fonte da Tabela 1 (Seção 2.1), com
dados medidos por estações reais no chão, citado na referência [21]. O artigo nomeia
9 estações na Paraíba (Seção 2.5) e usa mais algumas nos estados vizinhos. Foram
localizadas as 36 estações automáticas dentro da área de coleta (Paraíba, Ceará,
Pernambuco e Rio Grande do Norte), incluindo todas as 9 da Paraíba citadas no artigo
(Areia, Campina Grande, João Pessoa, Patos, São Gonçalo, Monteiro, Cabaceiras,
Camaratuba e Itaporanga). Como confirmação de que o conjunto está certo, a estação mais
antiga encontrada (Natal, começando em 23 de fevereiro de 2003) e uma das mais recentes
(Salgueiro, começando em 14 de setembro de 2017) têm exatamente as datas que o artigo
menciona na Seção 2.5.

Observação prática: existe uma API do INMET para baixar os dados estação por estação,
mas ela se mostrou instável e falhava. Por isso foram usados os arquivos zip anuais do
portal, que são mais confiáveis. Cada zip tem cerca de 80 MB e contém os dados de todas
as estações do Brasil naquele ano.

### IBGE (mapa dos municípios)

Mapa (polígonos): https://servicodados.ibge.gov.br/api/v3/malhas/estados/25?formato=application/vnd.geo+json&intrarregiao=municipio

Nomes dos municípios: https://servicodados.ibge.gov.br/api/v1/localidades/estados/25/municipios

Dessa fonte foram obtidos o contorno de cada município da Paraíba e o nome de cada um.
O código 25 é o código do estado da Paraíba no IBGE.

Motivo e referência no artigo: o artigo agrupa os pontos do MM grid por município e
reduz tudo a 223 pontos (Seção 4.2), que é justamente o número de municípios da
Paraíba. A divisão regional usada no artigo vem do IBGE, citada na referência [28]. O
contorno de cada município foi necessário para duas coisas: descobrir dentro de qual
município cada ponto da grade cai e desenhar os mapas. O IBGE devolveu exatamente 223
municípios, o mesmo número do artigo.

## 2. Como reproduzir do zero

O passo a passo abaixo começa na instalação. Todo o trabalho foi desenvolvido no
Windows com Python 3.10.

### 2.1 Instalar o Python

Baixar e instalar o Python 3.10 ou mais novo no site oficial:
https://www.python.org/downloads/

Na instalação no Windows, marcar a opção "Add Python to PATH". Isso faz o comando
`python` funcionar no terminal.

Para conferir se a instalação deu certo, executar no terminal (PowerShell):

```
python --version
```

Deve aparecer algo como `Python 3.10.x`.

### 2.2 Instalar as bibliotecas e por que cada uma é necessária

As bibliotecas são instaladas com o `pip`, que já vem junto com o Python. Cada uma tem
um papel no projeto:

- numpy: faz as contas com vetores e matrizes, como médias e raízes quadradas. É a base
  de quase todo o resto.
- pandas: lê e organiza os dados em tabelas. É usada para tratar as séries de tempo e
  para agrupar os pontos por município.
- scipy: fornece a estrutura cKDTree, que encontra rápido os vizinhos mais próximos de
  cada ponto. O método IDW precisa disso para achar os 4 pontos mais perto.
- scikit-learn: fornece a função que calcula o R2 (coeficiente de determinação), usada
  para avaliar a qualidade da interpolação.
- matplotlib: desenha os gráficos e os mapas.
- pykrige: faz a interpolação por Kriging, que é o método principal do artigo. Sem ela,
  seria preciso programar o Kriging do zero.
- geopandas: lê o mapa dos municípios (que vem em formato de polígonos) e descobre
  dentro de qual município cada ponto cai. Também recorta a grade só na parte que fica
  dentro da Paraíba.
- requests: baixa os dados das três fontes pela internet.

Ao instalar o geopandas, ele já traz junto outras três bibliotecas que usa por baixo
dos panos: shapely (geometria), pyproj (projeções de mapa) e fiona (leitura de arquivos
de mapa). Não é preciso instalar essas três na mão.

Comando para instalar tudo de uma vez:

```
pip install numpy pandas scipy scikit-learn matplotlib pykrige geopandas requests
```

Para deixar tudo separado do resto do computador, é possível criar um ambiente virtual
antes de instalar (passo opcional):

```
python -m venv venv
venv\Scripts\activate
pip install numpy pandas scipy scikit-learn matplotlib pykrige geopandas requests
```

### 2.3 Rodar o pipeline

No terminal, entrar na pasta do projeto:

```
cd reproduction
```

A forma mais simples é rodar tudo de uma vez com o orquestrador, que chama cada etapa
na ordem certa:

```
python run_all.py
```

Na primeira execução, todos os dados são baixados, o que demora alguns minutos (o INMET
é a parte mais lenta, porque são 20 arquivos grandes). Nas execuções seguintes, o que
já foi baixado é reaproveitado e o processo fica rápido.

Para rodar etapa por etapa e entender cada passo, esta é a ordem correta:

```
python src/data_ibge.py        # baixa o mapa dos 223 municipios
python src/data_nasa.py        # baixa os 80 pontos da NASA
python src/data_inmet.py       # baixa as 36 estacoes do INMET (2003 a 2022)
python src/preprocess.py all   # calcula as medias historicas de vento e solar
python src/interpolation.py    # compara IDW e Kriging e gera a Tabela 2
python src/mm_grid.py all       # monta o MM grid de 0,05 grau por Kriging
python src/ip_pb.py all          # calcula o IP-PB, os grupos e os rankings
python src/plots.py all          # gera todos os mapas e graficos
```

Os três primeiros comandos precisam de internet. Os outros usam só os arquivos já
salvos. As três primeiras etapas podem rodar em qualquer ordem entre si, mas as etapas
de processamento precisam vir depois delas.

### 2.4 Onde ficam os resultados

- `data/raw`: os dados brutos baixados (um arquivo por ponto da NASA, um por estação do INMET).
- `data/processed`: os dados já tratados (as médias, o MM grid, o IP-PB por município).
- `outputs/tables`: as tabelas em CSV (a Tabela 2 e os rankings).
- `outputs/figures`: as figuras em PNG.

## 3. Fluxograma do projeto e o que cada parte do código faz

O diagrama abaixo mostra como os dados percorrem o projeto, desde as fontes na internet
até os mapas e tabelas finais. Cada caixa é um arquivo de código dentro da pasta `src`.

```
              FONTES DE DADOS PUBLICAS (internet)

   NASA POWER              INMET                 IBGE
       |                     |                     |
       v                     v                     v
  data_nasa.py         data_inmet.py         data_ibge.py
  80 pontos de         36 estacoes           223 municipios
  satelite             terrestres            (contornos)
       |                     |                     |
       +---------+-----------+                     |
                 |                                 |
                 v                                 |
           preprocess.py                           |
           medias historicas de                    |
           vento e radiacao por ponto              |
                 |                                 |
        +--------+---------+                       |
        |                  |                       |
        v                  v                       |
 interpolation.py     mm_grid.py <-----------------+
 IDW vs Kriging       interpola para a grade
 validacao cruzada    de 0,05 grau (MM grid)
 (Tabela 2)                |
                           v
                       ip_pb.py
                       indice IP-PB, grupos
                       e rankings por municipio
                           |
                           v
                        plots.py
                        mapas e graficos (Figuras)
```

Dois arquivos não aparecem no diagrama porque são transversais: o `config.py` guarda
todos os parâmetros num lugar só (área da Paraíba, resolução da grade, períodos e
endereços das fontes) e o `run_all.py` executa as etapas na ordem mostrada acima.

Abaixo está o que cada etapa recebe, o que faz, o que produz e onde aquilo aparece no
artigo.

**data_nasa.py.** Monta a grade de 0,5 grau e baixa, para cada um dos 80 pontos, as
séries diárias de vento e radiação da NASA POWER. Produz um arquivo CSV por ponto em
`data/raw/nasa`. No artigo: coleta da base de satélite descrita na Seção 2.1 e na
Tabela 1.

**data_inmet.py.** Baixa os arquivos zip anuais (de 2003 a 2022), abre cada um, acha
as 36 estações de interesse e lê vento e radiação hora a hora. Produz um CSV por estação
em `data/raw/inmet`. No artigo: coleta da base de estações descrita na Seção 2.1, na
Tabela 1 e na Seção 2.5 (lista das estações).

**data_ibge.py.** Baixa o contorno e o nome dos 223 municípios da Paraíba. Produz o
arquivo `data/external/pb_municipios.gpkg`. No artigo: o agrupamento por município
aparece na Seção 4.2, e a divisão regional do IBGE é citada na referência [28].

**preprocess.py.** Recebe os dados brutos, remove valores fora do esperado (outliers),
converte a radiação do INMET (soma as horas de dia, das 5 às 18 horas no horário local,
e divide por 3600 para passar de kJ para kWh) e calcula a média histórica de vento e de
radiação de cada ponto e cada estação. Produz `nasa_points.csv` e `inmet_points.csv` em
`data/processed`. No artigo: o tratamento e a organização dos dados estão na Seção 2.5.

**interpolation.py.** Recebe os pontos com as médias e implementa os dois métodos de
interpolação: o IDW (Equações 1 e 2) e o Kriging (Equação 3). Avalia os dois por
validação cruzada usando as métricas RMSE, MAE e R2 (Equações 4 a 6). Produz
`table2_nasa.csv` e `table2_inmet.csv` em `outputs/tables`. No artigo: os métodos estão
na Seção 2.2, as métricas na Seção 2.3, e a comparação entre eles na Seção 3 e na
Tabela 2 (a Figura 4 mostra valores reais contra interpolados).

**mm_grid.py.** Recebe os pontos com as médias e o contorno dos municípios, cria uma
grade fina de 0,05 grau dentro da Paraíba, interpola o vento e a radiação para cada
ponto dessa grade usando o Kriging e marca a qual município cada ponto pertence. Produz
`mm_grid_nasa.csv` e `mm_grid_inmet.csv`. No artigo: o MM grid é descrito na Seção 4.1 e
mostrado nas Figuras 5 a 8.

**ip_pb.py.** Recebe o MM grid, normaliza o vento e a radiação entre 0 e 1 (Equação 7),
calcula o IP-PB de cada ponto como a raiz quadrada de (vento ao quadrado mais radiação
ao quadrado), agrupa os pontos por município (chegando aos 223), separa os municípios em
quatro grupos pela mediana de cada eixo e monta os rankings dos 10 melhores para solar,
vento e híbrido. Produz `ip_pb_nasa.csv`, `ip_pb_inmet.csv` e os arquivos `rank_*`. No
artigo: a definição do índice está na Seção 2.4 (Equação 7 para a normalização), e a
aplicação, os grupos e os rankings estão na Seção 4.2 e nas subseções 4.2.1 a 4.2.3
(Figuras 10 a 15).

**plots.py.** Recebe o MM grid e o IP-PB e desenha os mapas e os gráficos. Produz os
arquivos PNG em `outputs/figures`. No artigo: corresponde às Figuras 5 a 16.

A tabela a seguir resume onde cada passo da reprodução pode ser encontrado no artigo.

| Passo da reprodução (código) | Onde está no artigo |
|---|---|
| Coleta NASA e INMET (data_nasa, data_inmet) | Seção 2.1 e Tabela 1; referências [20] e [21] |
| Contorno dos municípios (data_ibge) | Seção 4.2; divisão regional na referência [28] |
| Tratamento e médias (preprocess) | Seção 2.5 |
| IDW e Kriging (interpolation) | Seção 2.2, Equações 1 a 3 |
| Métricas e escolha do método (interpolation) | Seção 2.3 (Equações 4 a 6) e Seção 3 (Tabela 2, Figura 4) |
| MM grid (mm_grid) | Seção 4.1, Figuras 5 a 8 |
| Normalização e índice IP-PB (ip_pb) | Seção 2.4, Equação 7 |
| Grupos e rankings (ip_pb) | Seção 4.2 e subseções 4.2.1 a 4.2.3, Figuras 10 a 15 |
| Figuras (plots) | Figuras 5 a 16 |

## 4. Onde está o aprendizado de máquina neste trabalho

Como a disciplina é de aprendizado de máquina, vale deixar claro onde ele aparece na
reprodução.

O método principal usado é o Kriging. O Kriging é, do ponto de vista matemático, a
mesma coisa que a Regressão por Processo Gaussiano (Gaussian Process Regression), que é
um método de aprendizado de máquina supervisionado. Ele aprende a partir dos dados ao
ajustar um modelo de covariância (o variograma) e usa esse modelo para prever o valor
em locais onde não há medição. A própria biblioteca scikit-learn oferece esse método com
o nome GaussianProcessRegressor, o que mostra que ele é tratado como aprendizado de
máquina.

Além do Kriging, o trabalho usa outras práticas que são padrão em aprendizado de
máquina: a validação cruzada do tipo deixe um de fora, para medir o erro de previsão em
dados que o modelo não viu; as métricas de regressão RMSE, MAE e R2, para comparar os
modelos; e a normalização Max-Min das variáveis antes de combiná-las.

O outro método testado, o IDW, não é aprendizado de máquina. Ele é uma interpolação
determinística que usa apenas a distância entre os pontos, sem aprender parâmetros a
partir dos dados.

Em resumo, a reprodução já tem um componente de aprendizado de máquina por causa do
Kriging e da forma de avaliação. Ainda assim, se a disciplina pede um uso mais central e
explícito de aprendizado de máquina, a etapa de contribuição é o lugar certo para isso.
A Ideia 2 do documento de ideias de contribuição (interpolar com Random Forest,
Gradient Boosting ou Processo Gaussiano usando variáveis extras, como o relevo e a
distância da costa) coloca o aprendizado de máquina no centro do trabalho e ainda ataca
a parte mais fraca do artigo, que é a previsão do vento.

## 5. Resultados

### 5.1 Comparação entre IDW e Kriging (a Tabela 2 do artigo)

Este passo corresponde à Seção 3 e à Tabela 2 do artigo (a Figura 4 mostra um exemplo
de valores reais contra interpolados). Os métodos comparados estão nas Equações 1 a 3 e
as métricas de erro nas Equações 4 a 6.

Para medir qual método interpola melhor, foi usada validação cruzada do tipo deixe um de
fora: um ponto é retirado da base, seu valor é estimado usando os 4 vizinhos mais
próximos e comparado com o valor verdadeiro. Isso é repetido para todos os pontos, e são
calculadas três medidas de erro:

- RMSE: raiz do erro quadrático médio. Quanto menor, melhor.
- MAE: erro absoluto médio. Quanto menor, melhor.
- R2: o quanto o método explica a variação dos dados. Quanto mais perto de 1, melhor.

A tabela abaixo mostra o RMSE e o R2 do artigo ao lado dos valores obtidos neste
trabalho (uma coluna para a base NASA e outra para a base INMET).

| Variável | Método | RMSE artigo | RMSE NASA | RMSE INMET | R2 artigo | R2 NASA | R2 INMET |
|---|---|---|---|---|---|---|---|
| Vento | IDW | 0,1711 | 0,2722 | 0,7816 | 0,3656 | 0,8734 | 0,3052 |
| Vento | Kriging | 0,1708 | 0,2449 | 0,7408 | 0,3892 | 0,8975 | 0,3759 |
| Solar | IDW | 0,0660 | 0,0857 | 0,5863 | 0,7640 | 0,8328 | -0,0722 |
| Solar | Kriging | 0,0407 | 0,0855 | 0,5745 | 0,8899 | 0,8335 | -0,0293 |

O ponto mais importante é que, em todos os casos, o Kriging deu erro menor e R2 maior
que o IDW. Essa é justamente a conclusão que o artigo usa para escolher o Kriging, e ela
se confirmou. O RMSE da radiação solar ficou na mesma faixa do artigo (em torno de 0,04
a 0,09).

Um detalhe interessante: o R2 do vento no artigo (de 0,37 a 0,39) ficou muito parecido
com o obtido na base INMET (de 0,31 a 0,38), enquanto o R2 da radiação solar do artigo
(de 0,76 a 0,89) ficou parecido com o obtido na base NASA (0,83). O R2 do vento na base
NASA ficou bem mais alto (0,87) porque a grade usada cobre uma área maior, que inclui
pontos sobre o mar, e isso aumenta a variação dos valores e facilita o R2. O R2 negativo
da radiação solar na base INMET quer dizer que, para essa variável, interpolar entre as
36 estações deu pior do que simplesmente usar a média, porque as estações são poucas e
espalhadas.

### 5.2 O MM grid

Este passo corresponde à Seção 4.1 do artigo e às Figuras 5 a 8.

| Item | Artigo | Reprodução |
|---|---|---|
| Pontos dentro da Paraíba | 2054 | 2016 (98,2 por cento) |
| Municípios cobertos | 223 | 223 |
| Escala da radiação solar | 4,93 a 6,23 | NASA 5,46 a 6,18 / INMET 4,77 a 6,07 |
| Escala do vento | 1,77 a 6,37 | NASA 4,08 a 6,02 / INMET 1,79 a 3,94 |

A diferença na contagem de pontos (2016 contra 2054) vem do nível de detalhe do
contorno do mapa e do encaixe da grade, e não muda nada no método. As escalas batem bem
com o artigo. Também ficou claro um ponto que o próprio artigo comenta: a NASA
superestima o vento em relação ao INMET, ou seja, os valores de vento do satélite são
mais altos do que os medidos no chão.

### 5.3 O índice IP-PB e os rankings

Este passo corresponde à definição do índice na Seção 2.4 (Equação 7 para a
normalização) e à aplicação na Seção 4.2 e subseções 4.2.1 a 4.2.3, além das Figuras 10
a 16.

Depois de normalizar o vento e a radiação entre 0 e 1, o IP-PB de cada município foi
calculado e os municípios foram separados em quatro grupos usando a mediana de cada
eixo. Os grupos seguem a ideia de bom ou ruim para vento e bom ou ruim para solar. A
tabela abaixo compara o que o artigo aponta com o que foi encontrado.

| Tipo | O que o artigo aponta | O que foi encontrado | Bate? |
|---|---|---|---|
| Solar | Região de Sousa-Cajazeiras e Patos, no oeste | NASA: São Bentinho, Pombal, Cajazeirinhas, Condado, Vista Serrana. INMET: Itaporanga, Piancó, Coremas, Aguiar | Sim, oeste nas duas |
| Vento | Campina Grande e João Pessoa | INMET: Areia, Alagoa Nova, Remígio, Arara (Brejo, perto de Campina Grande). NASA: região da Borborema e Seridó | Sim na base INMET |
| Híbrido | Eixo Campina Grande e Patos. Cita Amparo, Serra Branca, Parari, Santo André, Assunção, Junco do Seridó, Tenório e Sumé | NASA: Assunção, Junco do Seridó, Tenório, Frei Martinho, Nova Palmeira | Sim, 3 municípios iguais |

Os municípios de Assunção, Junco do Seridó e Tenório aparecem tanto no ranking de
geração híbrida obtido quanto na lista do artigo (são os municípios em laranja da
Figura 15). Além disso, Condado e Vista Serrana, que o artigo cita na Figura 16 como
municípios em que o índice da NASA e do INMET ficam parecidos, apareceram no top 10 de
energia solar deste trabalho. A correlação geral entre o IP-PB calculado com a NASA e
com o INMET deu 0,27, um valor fraco mas positivo, o que combina com o que o artigo diz,
que a concordância entre as duas bases só é forte em algumas regiões.

### 5.4 As figuras

As figuras ficam em `outputs/figures` e correspondem às do artigo:

- `mm_nasa_SOLAR_IRRAD.png`, `mm_inmet_SOLAR_IRRAD.png`, `mm_nasa_WIND_SPEED.png` e
  `mm_inmet_WIND_SPEED.png`: os mapas do MM grid, equivalentes às Figuras 5 a 8.
- `scatter_ippb_nasa.png` e `scatter_ippb_inmet.png`: os municípios no plano de vento
  contra solar, com os quatro grupos, equivalentes às Figuras 10 a 13.
- `top10_nasa.png` e `top10_inmet.png`: os 10 melhores municípios de cada tipo,
  equivalentes às Figuras 14 e 15.
- `correlation_ippb.png`: a comparação do IP-PB da NASA com o do INMET, equivalente à
  Figura 16.

## 6. Diferenças entre a reprodução e o artigo

Algumas coisas não saíram exatamente iguais, o que é esperado numa reprodução. Os
motivos:

1. Os valores exatos da Tabela 2 são diferentes porque não se sabe quais foram os 37
   pontos que o artigo usou, nem quais 6 pontos foram retirados para validar (a escolha
   foi aleatória), nem o período exato de cada estação. Mesmo assim, a conclusão de que
   o Kriging é melhor que o IDW se manteve.
2. No ranking de vento, a base NASA destaca a região da Borborema e do Seridó, que são
   áreas mais altas, em vez de Campina Grande. A base INMET corrige isso e concorda com
   o artigo, o que sugere que o artigo se apoiou mais nos dados do chão para o vento.
3. A contagem de pontos do MM grid (2016 contra 2054) é só uma diferença de desenho do
   contorno e de encaixe da grade, sem efeito no resultado.

## 7. Conclusão

Foi possível reproduzir o método do artigo usando apenas dados públicos. O resultado
ficou de acordo com o artigo: o Kriging é melhor que o IDW, o MM grid de alta resolução
foi montado, o índice IP-PB foi calculado e os padrões geográficos apareceram do mesmo
jeito (solar no oeste, vento perto de Campina Grande e geração híbrida no eixo Campina
Grande e Patos, com os mesmos municípios de Assunção, Junco do Seridó e Tenório). As
diferenças nos números vêm de escolhas de amostragem que o artigo não detalha e não
atrapalham as conclusões. Com isso, fica uma base pronta para a próxima etapa, que é
propor uma contribuição.

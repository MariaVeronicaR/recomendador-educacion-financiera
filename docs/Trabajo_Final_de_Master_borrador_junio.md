

**Universidad Internacional de la Rioja (UNIR) Escuela Superior de Ingenier´ıa y Tecnolog´ıa** 

**M´aster en Inteligencia Artificial** 

**Plataforma inteligente para la recomendaci´on personalizada de contenidos en educaci´on basada en financiera IA** 

#### **Trabajo Fin de Estudios** 

**Tipo de trabajo:** Desarrollo de software 

**Presentado por:** 

Mar´ıa Ver´onica Rodr´ıguez Mill´an 

Joaqu´ın Leandro Ram´ırez Huam´an 

**Dirigido por:** Felipe Miron Pozo 

Ciudad: Lima, Per´u / M´erida, M´exico Fecha: 21 de abril de 2026 

# **´Indice de Contenidos** 

|**Resum**|**en**||**VI**|
|---|---|---|---|
|**Abstra**|**ct**||**VII**|
|**1. Intr**|**oducc**|**i´on**|**1**|
|1.1.|Motiv|aci´on<br>. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|.<br>1|
||1.1.1.|Identifcaci´on del problema<br>. . . . . . . . . . . . . . . . . . . . . .|.<br>1|
||1.1.2.|Causas del problema . . . . . . . . . . . . . . . . . . . . . . . . . .|.<br>2|
||1.1.3.|Relevancia del problema . . . . . . . . . . . . . . . . . . . . . . . .|.<br>3|
|1.2.|Plant|eamiento del trabajo . . . . . . . . . . . . . . . . . . . . . . . . . . .|.<br>4|
||1.2.1.|La necesidad detectada<br>. . . . . . . . . . . . . . . . . . . . . . . .|.<br>4|
||1.2.2.|Qu´e se propone . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|.<br>5|
||1.2.3.|Finalidad de la intervenci´on . . . . . . . . . . . . . . . . . . . . . .|.<br>5|
|1.3.|Estru|ctura del trabajo . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|.<br>6|
|**2. Con**|**texto **|**y Estado del Arte**|**8**|
|2.1.|Alfab|etizaci´on Financiera: Defnici´on, Medici´on y||
||Brech|as<br>. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|.<br>8|
||2.1.1.|Defnici´on y marco conceptual<br>. . . . . . . . . . . . . . . . . . . .|.<br>8|
||2.1.2.|Medici´on estandarizada: Las “Big Three” . . . . . . . . . . . . . .|.<br>8|
||2.1.3.|Brechas espec´ıfcas en j´ovenes profesionales (22–30 a˜nos) . . . . . .|.<br>9|
|2.2.|Sistem|as de Recomendaci´on: Del Filtrado Colaborativo al Deep Learning|.<br>10|
||2.2.1.|Fundamentos de los Sistemas de Recomendaci´on (RecSys) . . . . .|.<br>10|
||2.2.2.|Neural Collaborative Filtering (NCF): El salto al Deep Learning .|.<br>11|
||2.2.3.|Knowledge Graphs en sistemas de recomendaci´on . . . . . . . . . .|.<br>13|
|2.3.|Machi<br>Apren|ne Learning para Personalizaci´on del<br>dizaje . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|.<br>15|



i 

|||Mar´ıa Ver´onica Rodr´ıguez<br>Joaqu´ın Leandro Ram´ırez <br>M´aster en Inteligencia A|Mill´an<br>Huam´an<br>rtifcial|
|---|---|---|---|
||2.3.1.|Educational Recommender Systems (ERS)<br>. . . . . . . . . . . . . .|15|
||2.3.2.|NLP para la categorizaci´on de contenido educativo . . . . . . . . . .|15|
|2.4.|Estado|del arte en RecSys aplicados a educaci´on fnanciera<br>. . . . . . . . .|15|
||2.4.1.|Sistemas basados en grafos de conocimiento y deep learning . . . . .|16|
||2.4.2.|Sistemas tutoriales inteligentes multiagente . . . . . . . . . . . . . .|16|
||2.4.3.|Aprendizaje autom´atico para la predicci´on de alfabetizaci´on fnanciera|16|
||2.4.4.|Algoritmos de targeting con aprendizaje autom´atico . . . . . . . . .|17|
||2.4.5.|Sistemas recomendadores educativos con grafos de conocimiento<br>. .|17|
||2.4.6.|Comparativa de trabajos relacionados . . . . . . . . . . . . . . . . .|17|
||2.4.7.|Vac´ıo identifcado . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|18|
|2.5.|Selecci|´on de arquitectura y justifcaci´on del stack||
||tecnol|´ogico<br>. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|19|
|2.6.|Selecci|´on de arquitectura y justifcaci´on del stack||
||tecnol|´ogico<br>. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|19|
||2.6.1.|Modelo de recomendaci´on: NeuMF . . . . . . . . . . . . . . . . . . .|19|
||2.6.2.|Grafo de conocimiento: Neo4j . . . . . . . . . . . . . . . . . . . . . .|20|
||2.6.3.|Motor de IA y backend<br>. . . . . . . . . . . . . . . . . . . . . . . . .|21|
||2.6.4.|Integraci´on KG-RecSys: estrategia de post-fltro<br>. . . . . . . . . . .|22|
|2.7.|Conclu|siones del estado del arte . . . . . . . . . . . . . . . . . . . . . . . . .|22|
|**3. Obj**|**etivos **|**y metodolog´ıa de**||
|**trab**|**ajo**||**24**|
|3.1.|Objeti|vos del trabajo . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|24|
|**4. Ide**|**ntifcac**|**i´on de Requisitos**|**25**|
|4.1.|Introd|ucci´on . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|25|
|4.2.|Identif|caci´on del problema<br>. . . . . . . . . . . . . . . . . . . . . . . . . . .|25|
|4.3.|Usuari|o objetivo<br>. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|25|
|4.4.|Conte|xto de uso<br>. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|26|



ii 

||Mar´ıa Ver´onica Rodr´ıguez Mill´an|
|---|---|
||Joaqu´ın Leandro Ram´ırez Huam´an<br>M´aster en Inteligencia Artifcial|
|4.5. Requisitos funcionales<br>. . . . . . . . . . . .|. . . . . . . . . . . . . . . . . .<br>26|
|4.6. Requisitos no funcionales<br>. . . . . . . . . .|. . . . . . . . . . . . . . . . . .<br>26|
|4.7. Requisitos de datos . . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . .<br>27|
|4.8. Requisitos pedag´ogicos . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . .<br>27|
|4.9. Requisitos de seguridad fnanciera<br>. . . . .|. . . . . . . . . . . . . . . . . .<br>28|
|4.10. Requisitos del sistema de recomendaci´on . .|. . . . . . . . . . . . . . . . . .<br>28|
|4.11. Requisitos del grafo de conocimiento . . . .|. . . . . . . . . . . . . . . . . .<br>28|
|4.12. Conclusiones del cap´ıtulo<br>. . . . . . . . . .|. . . . . . . . . . . . . . . . . .<br>29|
|**5. Descripci´on de la herramienta**||
|**software desarrollada**|**30**|
|5.1. Descripci´on . . . . . . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . .<br>30|
|5.1.1.<br>Objetivo de la herramienta<br>. . . . .|. . . . . . . . . . . . . . . . . .<br>30|
|5.1.2.<br>Proceso de desarrollo . . . . . . . . .|. . . . . . . . . . . . . . . . . .<br>30|
|5.1.3.<br>Arquitectura general . . . . . . . . .|. . . . . . . . . . . . . . . . . .<br>31|
|5.1.4.<br>Componentes principales<br>. . . . . .|. . . . . . . . . . . . . . . . . .<br>32|
|5.1.5.<br>Tecnolog´ıas utilizadas<br>. . . . . . . .|. . . . . . . . . . . . . . . . . .<br>32|
|5.1.6.<br>Funcionamiento de la aplicaci´on<br>. .|. . . . . . . . . . . . . . . . . .<br>32|
|5.1.7.<br>Pantallas principales . . . . . . . . .|. . . . . . . . . . . . . . . . . .<br>33|
|5.1.8.<br>Integraci´on de los componentes . . .|. . . . . . . . . . . . . . . . . .<br>34|
|5.1.9.<br>Resultado obtenido . . . . . . . . . .|. . . . . . . . . . . . . . . . . .<br>34|
|5.1.10. Conclusi´on<br>. . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . .<br>34|
|**6. Conclusiones y Trabajo Futuro**|**35**|
|Referencias<br>. . . . . . . . . . . . . . . . . . . . .|. . . . . . . . . . . . . . . . . .<br>35|
|**A. Apendices**|**38**|



iii 

# **´Indice de Ilustraciones** 

|2.1. Uso de un grafo de conocimiento como post-fltro en un sistema de reco-||
|---|---|
|mendaci´on educativo . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|14|
|6.1. Logo Unir . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|35|



iv 

# **´Indice de Tablas** 

|2.1. Comparativa de trabajos relacionados en RecSys aplicados a educaci´on f-||
|---|---|
|nanciera y sistemas educativos con grafos de conocimiento . . . . . . . . . .|18|
|4.1. Perfl del usuario objetivo . . . . . . . . . . . . . . . . . . . . . . . . . . . .|26|
|5.1. Fases del proceso de desarrollo<br>. . . . . . . . . . . . . . . . . . . . . . . . .|31|
|5.2. Tecnolog´ıas utilizadas en el prototipo . . . . . . . . . . . . . . . . . . . . . .|32|
|6.1. Tabla 1<br>. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|35|



v 

# **Resumen** 

**Nota:** En este apartado se introducir´a un breve resumen en espa˜nol del trabajo realizado (extensi´on m´axima: 150 palabras). Este resumen debe incluir el objetivo o prop´osito de la investigaci´on, la metodolog´ıa, los resultados y las conclusiones. 

LO ESTAMOS DEJANDO PARA EL FINAL 

**Palabras Clave:** Se deben incluir de 3 a 5 palabras claves en espa˜nol 

vi 

# **Abstract** 

**Nota:** En este apartado se introducir´a un breve resumen en espa˜nol del trabajo realizado (extensi´on m´axima: 150 palabras). Este resumen debe incluir el objetivo o prop´osito de la investigaci´on, la metodolog´ıa, los resultados y las conclusiones. 

LO ESTAMOS DEJANDO PARA EL FINAL 

**Palabras Clave:** Se deben incluir de 3 a 5 palabras claves en ingl´es 

vii 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

viii 

# **1. Introducci´on** 

## **1.1. Motivaci´on** 

### **1.1.1. Identificaci´on del problema** 

El problema central de este trabajo es la existencia de una brecha cr´ıtica entre la capacidad de ahorro de los j´ovenes profesionales espa˜noles (18–34 a˜nos) y su nivel de alfabetizaci´on financiera. 

A pesar de encontrarse en una etapa vital determinante —caracterizada por la incorporaci´on al mercado laboral y la formaci´on del hogar—, este colectivo presenta dificultades para transformar el ahorro acumulado en una planificaci´on financiera eficiente. Esta situaci´on refleja una desconexi´on entre la capacidad de ahorro y la capacidad de gesti´on financiera efectiva, limitando la generaci´on de patrimonio y estabilidad econ´omica futura. Seg´un los resultados de la Encuesta de Competencias Financieras (ECF) 2021 del Banco de Espa˜na, los individuos de entre 18 y 34 a˜nos han mejorado su nivel promedio de conocimientos financieros, pasando de un 46 % de respuestas correctas en 2016 a un 52 % en 2021. No obstante, este avance contin´ua mostrando carencias significativas en conceptos financieros fundamentales. 

En particular, ´unicamente el 44 % de los j´ovenes respondi´o correctamente a la pregunta relacionada con el inter´es compuesto, porcentaje inferior al obtenido en conceptos como inflaci´on (60 %) o diversificaci´on del riesgo (50 %). Esta situaci´on evidencia dificultades en la comprensi´on del crecimiento acumulativo del capital y de los efectos que la inflaci´on puede generar sobre el valor real del ahorro a largo plazo. (Hospido, Machelett, Pidkuyko, y Villanueva, 2023) 

Esta carencia de conocimientos financieros no es ´unicamente te´orica, sino que tambi´en se refleja en los h´abitos de ahorro y en la utilizaci´on de instrumentos financieros por parte de la poblaci´on joven. Seg´un la Encuesta de Competencias Financieras (ECF) 2021 del Banco de Espa˜na, el 87 % de los individuos entre 18 y 34 a˜nos afirma haber ahorrado durante los ´ultimos doce meses, situ´andose como el grupo con mayor propensi´on al ahorro. Sin embargo, gran parte de este ahorro se concentra en mecanismos de baja rentabilidad y escasa protecci´on frente a la inflaci´on. 

1 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

Entre los j´ovenes que han ahorrado, el 67 % utiliza cuentas corrientes como principal medio de ahorro y el 60 % conserva dinero en efectivo fuera del sistema financiero. En contraste, ´unicamente un 6 % declara utilizar fondos de inversi´on y un 3 % planes de pensiones como instrumentos de ahorro. Estos resultados evidencian una preferencia por formas de ahorro de elevada liquidez, pero con limitada capacidad de generaci´on de rentabilidad real a largo plazo. 

Finalmente, los enfoques tradicionales de educaci´on financiera se enfrentan a un entorno de complejidad creciente. Los j´ovenes profesionales hoy operan en una econom´ıa digitalizada y a menudo se enfrentan a la inestabilidad de ingresos propia de la econom´ıa de plataforma o contratos temporales, lo que requiere una capacidad de planificaci´on y resiliencia mucho mayor que en d´ecadas anteriores. Los modelos de formaci´on est´aticos y generales han demostrado ser insuficientes, ya que no logran personalizar el aprendizaje seg´un el comportamiento real del usuario ni mitigar los nuevos riesgos digitales, como la la promoci´on de productos financieros complejos mediante din´amicas digitales altamente interactivas o los fraudes en entornos en l´ınea. 

La creciente digitalizaci´on de este grupo poblacional ofrece una oportunidad significativa para abordar esta problem´atica desde una perspectiva tecnol´ogica. Los j´ovenes presentan una alta interacci´on con entornos digitales, lo que genera una mayor disponibilidad de datos comportamentales y de consumo, facilitando el desarrollo de soluciones m´as precisas y adaptativas. 

En este contexto, la inteligencia artificial y los sistemas de recomendaci´on permiten desarrollar plataformas capaces de analizar patrones de comportamiento financiero y adaptar din´amicamente los contenidos educativos seg´un las caracter´ısticas y necesidades del usuario. De este modo, se propone el desarrollo de una plataforma inteligente de recomendaci´on de contenidos en educaci´on financiera basada en IA, orientada a mejorar la toma de decisiones y fomentar una gesti´on activa y eficiente de los recursos econ´omicos en los j´ovenes profesionales. 

### **1.1.2. Causas del problema** 

Las causas de esta situaci´on son multidimensionales y pueden categorizarse en tres ejes: 

1. **Falta de educaci´on formal adaptada:** El sistema educativo tradicional en Espa˜na no integra de manera transversal la educaci´on financiera en los planes de estudio. 

2 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

Cuando esta formaci´on existe, suele ser predominantemente te´orica y escasamente vinculada a la realidad digital actual, caracterizada por el uso de aplicaciones de inversi´on, plataformas fintech y nuevos instrumentos financieros digitales. 

2. **Sesgos cognitivos y psicol´ogicos:** Los j´ovenes profesionales est´an expuestos a diversos sesgos conductuales que afectan su toma de decisiones financieras. Entre ellos destacan el overconfidence bias (exceso de confianza en sus propios conocimientos) y el present bias (preferencia por recompensas inmediatas frente a beneficios futuros), lo que conduce a priorizar el consumo o el ahorro a corto plazo en detrimento de estrategias de inversi´on a largo plazo. 

3. **Complejidad y “ruido” digital:** La digitalizaci´on ha generado una sobreabundancia de informaci´on y un acceso masivo a productos financieros complejos, como criptoactivos o servicios de financiaci´on inmediata (BNPL). La ausencia de herramientas de filtrado y personalizaci´on provoca que los j´ovenes se enfrenten a un entorno informativo saturado, lo que puede derivar en decisiones basadas en fuentes no especializadas o tendencias de redes sociales, en lugar de criterios t´ecnicos fundamentados. 

### **1.1.3. Relevancia del problema** 

Este problema es de vital importancia tanto para la comunidad cient´ıfica como para la sociedad por las siguientes razones: 

- **Impacto en la estabilidad econ´omica:** La dificultad para superar la denominada “barrera del ahorro inicial” limita el acceso a activos clave como la vivienda. Esta barrera se estima en torno al 30–32 % del valor del inmueble, considerando aproximadamente un 20 % de entrada no financiada por entidades bancarias y un 10–12 % adicional correspondiente a impuestos y gastos asociados. Esta situaci´on retrasa hitos vitales fundamentales y reduce la capacidad de generaci´on de riqueza a largo plazo en los j´ovenes profesionales. 

- **Vulnerabilidad ante fraudes:** La insuficiente alfabetizaci´on financiera, especialmente en entornos digitales, incrementa la exposici´on a ciberestafas, productos financieros de alto riesgo y decisiones de inversi´on mal fundamentadas. En un contexto de creciente digitalizaci´on, esta vulnerabilidad representa un riesgo significativo para la estabilidad econ´omica individual. 

3 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

- **Relevancia para la investigaci´on y la innovaci´on educativa:** Desde el ´ambito acad´emico, existe una creciente necesidad de explorar nuevas metodolog´ıas que mejoren la educaci´on financiera. En este sentido, la inteligencia artificial se presenta como una herramienta clave para transformar los modelos tradicionales, permitiendo el desarrollo de sistemas adaptativos capaces de personalizar el aprendizaje en funci´on del perfil, comportamiento y necesidades espec´ıficas de cada usuario. En conjunto, estos factores evidencian la necesidad de desarrollar soluciones innovadoras que no solo aborden la falta de conocimientos financieros, sino que tambi´en faciliten su aplicaci´on pr´actica mediante enfoques personalizados y basados en datos, como los que permite la inteligencia artificial. 

## **1.2. Planteamiento del trabajo** 

### **1.2.1. La necesidad detectada** 

El problema identificado no se limita ´unicamente a la falta de educaci´on financiera, sino tambi´en a la ausencia de mecanismos de personalizaci´on en la distribuci´on de contenidos educativos. Los sistemas actuales de educaci´on financiera —tanto aplicaciones de fintech como plataformas de _e-learning_ — operan con l´ogicas de recomendaci´on rudimentarias: filtros por categor´ıas manuales, listados est´aticos de “cursos populares” o, en el mejor de los casos, algoritmos cl´asicos de recomendaci´on basados en filtrado colaborativo que no consideran las relaciones de dependencia y progresi´on existentes entre los distintos conceptos financieros. 

Desde la perspectiva de la Inteligencia Artificial, esto presenta tres deficiencias t´ecnicas: 

1. **Limitaciones asociadas al problema de “Cold Start” pedag´ogico:** Cuando un usuario nuevo accede al sistema, no existe un historial previo de interacci´on del usuario con la plataforma. Los sistemas tradicionales no pueden recomendar nada relevante. Un modelo de IA debe poder inferir un perfil inicial a partir de datos demogr´aficos y una evaluaci´on diagn´ostica. 

2. **Falta de modelado del conocimiento:** Las finanzas personales no son un conjunto de temas independientes. Existen relaciones de prerrequisito estrictas (ej. no se puede entender “fondos indexados” sin dominar “diversificaci´on” e “inter´es compuesto”). Los sistemas actuales no modelan adecuadamente estas relaciones de dependencia 

4 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

entre conceptos financieros. 

3. **Ausencia de aprendizaje secuencial:** La educaci´on es un proceso temporal. Un sistema de IA debe optimizar no la relevancia de una ´unica recomendaci´on, sino una secuencia progresiva de contenidos educativos adaptados al nivel del usuario que favorezca una mejor asimilaci´on progresiva del conocimiento financiero. 

Con ello, se busca mejorar la experiencia de aprendizaje financiero mediante recomendaciones m´as relevantes, adaptativas y alineadas con las necesidades reales de cada usuario. 

### **1.2.2. Qu´e se propone** 

Ante estas limitaciones, se propone el desarrollo de una plataforma inteligente de educaci´on financiera personalizada, basada en la integraci´on de t´ecnicas de aprendizaje profundo y grafos de conocimiento. El n´ucleo del sistema combinar´a un modelo h´ıbrido de recomendaci´on (NeuMF) capaz de aprender patrones complejos de interacci´on usuario-contenido, con un grafo de conocimiento que modele las dependencias pedag´ogicas entre conceptos financieros. De este modo, las recomendaciones ser´an simult´aneamente personalizadas al perfil del usuario y coherentes con la progresi´on l´ogica del aprendizaje. 

La materializaci´on de la propuesta se concretar´a en un prototipo web funcional que permita validar la viabilidad t´ecnica y pedag´ogica del enfoque. El usuario completar´a un cuestionario inicial de perfilado, recibir´a un itinerario de aprendizaje adaptado y avanzar´a mediante m´odulos con evaluaciones formativas que retroalimenten al modelo. 

La justificaci´on detallada de esta arquitectura, as´ı como el an´alisis comparativo frente a otras alternativas existentes en la literatura, se presenta en el cap´ıtulo 2 (Contexto y Estado del Arte). El cap´ıtulo 3 describe la metodolog´ıa completa, el cap´ıtulo 4 la implementaci´on y resultados experimentales, y el cap´ıtulo 5 las conclusiones y l´ıneas futuras. 

### **1.2.3. Finalidad de la intervenci´on** 

La finalidad es doble: 

1. **Cient´ıfica:** Evaluar el impacto de la integraci´on de Knowledge Graphs con arquitecturas de Neural Collaborative Filtering sobre m´etricas de recomendaci´on (NDCG@k, Precision@k) y sobre la coherencia pedag´ogica del itinerario formativo. 

2. **Aplicada:** Entregar un prototipo funcional validado que sirva como prueba de concepto para una plataforma de educaci´on financiera personalizada,demostrando el 

5 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

potencial de la IA para proporcionar experiencias de aprendizaje financiero m´as personalizadas y adaptativas. 

## **1.3. Estructura del trabajo** 

Para abordar el problema y la propuesta descritos en los apartados anteriores, la memoria se organiza en cinco cap´ıtulos, siguiendo una progresi´on l´ogica que va desde la identificaci´on del problema hasta la validaci´on emp´ırica del prototipo: 

- **Cap´ıtulo 1: Introducci´on.** Este cap´ıtulo establece las bases del trabajo. Se identifica el problema de la brecha de alfabetizaci´on financiera en j´ovenes profesionales espa˜noles, se justifica su relevancia desde las perspectivas social y tecnol´ogica, y se plantea la propuesta de un sistema de recomendaci´on basado en aprendizaje profundo como soluci´on. Finalmente, se definen los objetivos generales y espec´ıficos que guiar´an el desarrollo del proyecto. 

- **Cap´ıtulo 2: Contexto y Estado del Arte.** Se revisa la literatura cient´ıfica fundamental para contextualizar el trabajo. Se analizan tres bloques tem´aticos: (i) los fundamentos de la alfabetizaci´on financiera y las brechas detectadas en la poblaci´on objetivo; (ii) los sistemas de recomendaci´on tradicionales y sus limitaciones en entornos educativos; y (iii) las arquitecturas de _Neural Collaborative Filtering_ y el uso de _Knowledge Graphs_ como v´ıas para superar dichas limitaciones. 

- **Cap´ıtulo 3: Objetivos concretos y metodolog´ıa de trabajo.** Describe la arquitectura completa del sistema propuesto. Se detalla el pipeline de datos: obtenci´on y preprocesamiento de datasets (ECF 2021, metadatos de cursos), dise˜no del modelo NeuMF, construcci´on del grafo de conocimiento financiero, y la estrategia de integraci´on entre ambos componentes. 

- **Cap´ıtulo 4: Identificaci´on de Requisitos.** Este cap´ıtulo presenta el trabajo previo realizado para orientar el desarrollo del software. Se identifica el problema a tratar, el perfil de usuario objetivo y el contexto habitual de uso de la aplicaci´on. Asimismo, se definen los requisitos funcionales, no funcionales, pedag´ogicos, de datos y de seguridad financiera que debe cumplir el prototipo. Esta fase permite establecer una base clara para el dise˜no posterior del sistema de recomendaci´on y del grafo de conocimiento. 

- **Cap´ıtulo 5: Descripci´on de la Herramienta Software Desarrollada.** Este 

6 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

cap´ıtulo describe el prototipo software desarrollado como resultado del trabajo. Se documentan las fases principales del proceso de desarrollo, los hitos alcanzados, el stack tecnol´ogico utilizado y la arquitectura general de la aplicaci´on. Tambi´en se presentan diagramas explicativos del funcionamiento del sistema, el flujo de interacci´on del usuario y capturas de pantalla que permiten comprender el comportamiento del programa. El prototipo integra una aplicaci´on web, una API desarrollada con FastAPI, un modelo de recomendaci´on, un grafo de conocimiento y una interfaz de usuario para la recomendaci´on personalizada de contenidos educativos. 

**Cap´ıtulo 6: Conclusiones y L´ıneas Futuras.** Se sintetizan los logros alcanzados en relaci´on con los objetivos planteados, se reflexiona sobre las limitaciones del sistema desarrollado y se proponen v´ıas de mejora y escalabilidad. 

Adicionalmente, la memoria incluye una secci´on de Referencias Bibliogr´aficas que recoge las fuentes acad´emicas, t´ecnicas e institucionales citadas a lo largo del documento. Asimismo, se incorporan anexos con material complementario del proyecto, incluyendo el enlace al repositorio donde se aloja el c´odigo fuente, los datos utilizados y los recursos necesarios para reproducir el prototipo. 

7 

# **2. Contexto Estado del Arte y** 

## **2.1. Alfabetizaci´on Financiera: Definici´on, Medici´on y Brechas** 

### **2.1.1. Definici´on y marco conceptual** 

La alfabetizaci´on financiera ha evolucionado desde un concepto meramente informativo hacia una competencia multidimensional. La definici´on m´as ampliamente aceptada en la literatura econ´omica es la propuesta por Lusardi y Mitchell (Lusardi y Mitchell, 2014), quienes la conciben como el conocimiento de los conceptos financieros b´asicos necesarios para tomar decisiones econ´omicas informadas. 

La OCDE/INFE, en la _International Survey of Adult Financial Literacy_ , propone un modelo de tres dimensiones para operacionalizar la medici´on de la alfabetizaci´on financiera: conocimientos financieros, comportamiento financiero y actitud financiera (Organisation for Economic Co-operation and Development, 2023). 

1. **Conocimientos financieros (** **_Financial Knowledge_ ):** Comprensi´on de conceptos clave como inflaci´on, inter´es compuesto, diversificaci´on y relaci´on riesgo-rentabilidad. 

2. **Comportamiento financiero (** **_Financial Behaviour_ ):** Pr´acticas concretas de gesti´on del dinero (presupuestaci´on, ahorro regular, planificaci´on de jubilaci´on). 

3. **Actitud financiera (** **_Financial Attitude_ ):** Disposici´on psicol´ogica hacia el largo plazo frente al corto plazo, la propensi´on al riesgo y la dependencia del endeudamiento. 

Este marco tripartito resulta especialmente relevante para el presente trabajo porque permite identificar que un usuario puede tener conocimientos te´oricos pero un comportamiento sub´optimo, lo cual refuerza la necesidad de un sistema que no solo ense˜ne, sino que modele y acompa˜ne la conducta. 

### **2.1.2. Medici´on estandarizada: Las “Big Three”** 

El instrumento de medici´on m´as difundido internacionalmente son las denominadas _Big Three questions_ , desarrolladas por Lusardi y Mitchell y adoptadas por la OCDE, el Banco 

8 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

de Espa˜na y otras instituciones. Las preguntas eval´uan: 

- **Inter´es compuesto:** Si tienes 100€ a un inter´es del 2 % anual, ¿cu´anto tendr´as al cabo de 5 a˜nos? 

- **Inflaci´on:** Si la tasa de inter´es de una cuenta de ahorro es del 1 % anual y la inflaci´on del 2 %, ¿puedes comprar m´as, lo mismo o menos dentro de un a˜no? **Diversificaci´on:** ¿Es cierto que una cartera de inversi´on con un solo activo es generalmente menos riesgosa que una cartera con m´ultiples activos? 

Los resultados de la ECF 2021 (Hospido y cols., 2023) en Espa˜na revelan patrones cr´ıticos para el segmento objetivo de este TFM: 

- Solo el 46 % de la poblaci´on adulta responde correctamente a las tres preguntas. En el tramo de 18–34 a˜nos, el porcentaje desciende al 17 %, con una brecha significativa entre hombres y mujeres. 

- El 83 % de los j´ovenes espa˜noles acierta en la pregunta de inflaci´on, pero el rendimiento cae dr´asticamente en inter´es compuesto (47 %) y diversificaci´on (49 %). 

### **2.1.3. Brechas espec´ıficas en j´ovenes profesionales (22–30 a˜nos)** 

El colectivo de j´ovenes profesionales presenta caracter´ısticas diferenciales que justifican un tratamiento espec´ıfico respecto a otros segmentos etarios. 

#### **a) Paradoja del ahorro pasivo** 

A pesar de ser el grupo con mayor propensi´on al ahorro, la gesti´on del ahorro es marcadamente pasiva. Los j´ovenes profesionales concentran sus activos l´ıquidos en productos de bajo riesgo y nula rentabilidad real, mientras que la inversi´on en productos de renta variable o planes de pensiones es marginal. 

#### **b) Brecha de vivienda y “trampa del alquiler”** 

El acceso a la vivienda constituye el principal objetivo de ahorro de los j´ovenes profesionales espa˜noles. Sin embargo, la conjunci´on de precios de vivienda elevados, salarios de entrada contenidos y la exigencia de un ahorro inicial del 32 % convierte este hito en inalcanzable para la mayor´ıa. 

9 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

#### **c) Digitalizaci´on sin criterio: criptoactivos y fintech** 

El acceso facilitado por aplicaciones m´oviles ha democratizado la inversi´on, pero no la educaci´on sobre riesgos asociados. Esto incrementa la exposici´on a decisiones financieras mal informadas. 

#### **d) Sesgos cognitivos** 

La literatura de econom´ıa conductual identifica sesgos particularmente prevalentes en este grupo: 

- **Sobreconfianza:** Tendencia a sobrestimar la propia capacidad de predicci´on y conocimiento financiero, lo que conduce a subestimar riesgos y descartar formaci´on introductoria percibida como innecesaria. 

- **Sesgo de presente:** Preferencia desproporcionada por recompensas inmediatas frente a mayores beneficios futuros, manifestada en la concentraci´on del ahorro en instrumentos l´ıquidos de baja rentabilidad real. 

- **Efecto de anclaje:** dependencia excesiva de la primera informaci´on recibida (precio de referencia, opini´on inicial o dato visto en redes sociales) al formular juicios y decisiones posteriores. 

## **2.2. Sistemas de Recomendaci´on: Del Filtrado Colaborativo al Deep Learning** 

### **2.2.1. Fundamentos de los Sistemas de Recomendaci´on (RecSys)** 

Los sistemas de recomendaci´on son herramientas de software que predicen la utilidad o preferencia que un usuario tendr´a por un ´ıtem no visto, bas´andose en datos hist´oricos de interacciones usuario-´ıtem. Su objetivo es mitigar la sobrecarga de informaci´on presentando al usuario un subconjunto filtrado de ´ıtems potencialmente relevantes (Zhang, Yao, Sun, y Tay, 2019). 

Tradicionalmente, los RecSys se clasifican en tres paradigmas: 

1. **Filtrado Colaborativo (CF):** El CF infiere las preferencias de un usuario a partir de la similitud con otros usuarios (user-based) o de la similitud entre ´ıtems (itembased). La t´ecnica m´as representativa es la factorizaci´on matricial (Matrix Factorization, MF), que descompone la matriz de interacciones usuario-´ıtem en dos matrices 

10 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

de embeddings de menor dimensi´on. Aunque eficaz en escenarios con abundantes datos de interacci´on, el CF puro presenta dos limitaciones cr´ıticas en el contexto de este trabajo: el problema del cold start (usuarios nuevos sin historial de interacci´on con la plataforma) y la incapacidad para incorporar atributos contextuales del usuario (edad, nivel de ingresos, perfil de riesgo) que son fundamentales para personalizar contenidos de educaci´on financiera, limitaciones ampliamente documentadas en la literatura de sistemas de recomendaci´on (Zhang y cols., 2019). 

2. **Filtrado Basado en Contenido (CB):** El CB recomienda ´ıtems similares a aquellos que el usuario ha consumido previamente, bas´andose en la similitud de atributos entre usuarios e´ıtems. En el ´ambito educativo, esto traduce a recomendar contenidos cuya dificultad, formato o tem´atica se alineen con el perfil del estudiante. Su principal ventaja es que no requiere datos de otros usuarios, mitigando parcialmente el cold start. Sin embargo, su limitaci´on m´as severa es la overspecialization: al recomendar siempre contenidos similares a los ya consumidos, el sistema ignora patrones colectivos de aprendizaje y dificulta la descubribilidad de nuevos temas necesarios para una formaci´on completa. En educaci´on financiera, esto equivaldr´ıa a encasillar al usuario en su zona de confort (presupuesto y ahorro) sin impulsarle hacia conceptos m´as avanzados (inversi´on, jubilaci´on). 

3. **M´etodos H´ıbridos:** Los m´etodos h´ıbridos combinan CF y CB para superar las limitaciones individuales de cada paradigma, reduciendo problemas como el cold start y la overspecialization (Zhang y cols., 2019). En escenarios educativos, los h´ıbridos permiten aprovechar tanto los patrones colectivos de aprendizaje como las caracter´ısticas individuales del estudiante. No obstante, las arquitecturas h´ıbridas cl´asicas (por ejemplo, factorizaci´on matricial con side information) siguen estando limitadas por la naturaleza lineal de sus funciones de interacci´on, lo que dificulta captar relaciones complejas entre m´ultiples variables contextuales. 

### **2.2.2. Neural Collaborative Filtering (NCF): El salto al Deep Learning** 

El trabajo seminal de He et al. (He y cols., 2017a) representa un punto de inflexi´on en los RecSys. Los autores proponen el _Neural Collaborative Filtering (NCF)_ , un marco que sustituye el producto escalar lineal de la factorizaci´on matricial por una red neuronal multicapa capaz de aprender funciones de interacci´on arbitrarias. 

11 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

La arquitectura NCF se compone de dos representaciones fundamentales que pueden combinarse de forma modular: 

- **GMF (Generalized Matrix Factorization):** Extiende la factorizaci´on matricial tradicional permitiendo un producto elemento a elemento aprendido (*element-wise product*) entre los embeddings de usuario e ´ıtem, seguido de una activaci´on lineal con peso aprendible. Esta componente preserva la capacidad del CF cl´asico para capturar patrones globales de interacci´on usuario-contenido, es decir, tendencias colectivas del tipo .<sup>a</sup> usuarios con perfil similar le result´o ´util este contenido”. 

- **MLP (Multi-Layer Perceptron):** Concatena los embeddings de usuario e ´ıtem y los procesa a trav´es de capas densas con activaciones no lineales (ReLU, habitualmente). El MLP aprende relaciones complejas a partir de variables contextuales: edad, nivel de ingresos, propensi´on al ahorro, conocimientos previos del usuario, as´ı como dificultad, formato o tem´atica del contenido educativo. Esta componente es la que permite al modelo personalizar la recomendaci´on a perfiles heterog´eneos, como los j´ovenes profesionales espa˜noles con niveles dispares de alfabetizaci´on financiera. 

La arquitectura **NeuMF** (Neural Matrix Factorization) surge de la concatenaci´on de las salidas de GMF y MLP en una capa de predicci´on final: 



Donde _pu_ y _qi_ son los embeddings de usuario e ´ıtem, _ϕGMF_ y _ϕMLP_ son las funciones de transformaci´on de cada componente, _h_<sup>_T_</sup> es el vector de pesos de la capa de salida y _σ_ la funci´on de activaci´on (t´ıpicamente sigmoide para predicci´on de probabilidad de interacci´on). 

**Justificaci´on de NeuMF para educaci´on financiera** . NeuMF cl´asico (He y cols., 2017b) modela ´unicamente interacciones entre embeddings de usuario e ´ıtem, combinando patrones globales (GMF) con relaciones no lineales aprendidas por el MLP. Sin embargo, en este dominio la utilidad pedag´ogica de un contenido depende tambi´en de caracter´ısticas contextuales del usuario: edad, nivel de ingresos, conocimientos previos o perfil de riesgo. Para incorporar estas variables, se propone una variante **feature-aware NeuMF** que enriquece el vector de entrada del MLP con caracter´ısticas demogr´aficas y diagn´osticas del usuario adem´as de sus embeddings. Esta extensi´on, com´un en la literatura de sistemas de 

12 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

recomendaci´on h´ıbridos, permite mitigar el **cold start** pedag´ogico: incluso para un usuario sin historial de interacci´on en la plataforma, el modelo puede inferir un perfil inicial a partir de sus respuestas al cuestionario de perfilado. As´ı, la arquitectura base (NeuMF) captura patrones de interacci´on usuario-contenido, mientras que el enriquecimiento con variables contextuales habilita la personalizaci´on a perfiles heterog´eneos. 

### **2.2.3. Knowledge Graphs en sistemas de recomendaci´on** 

Los Grafos de Conocimiento (KG) son estructuras de datos que representan entidades y sus relaciones sem´anticas mediante nodos y aristas. En el ´ambito de los RecSys, los KG aportan informaci´on estructurada que los modelos tradicionales no capturan, constituyendo una de las l´ıneas m´as relevantes en la evoluci´on reciente de los sistemas de recomendaci´on (Guo y cols., 2020). 

Existen tres formas principales de integrar KG en recomendadores, especialmente en arquitecturas h´ıbridas basadas en Deep Learning (Gao, Li, Lin, Gao, y Khan, 2020), con distintos niveles de acoplamiento con el modelo de predicci´on: 

1. **KG como restricci´on (post-filtro o pre-filtro):** El modelo de recomendaci´on genera un ranking de candidatos y el grafo filtra aquellos que violan restricciones sem´anticas. En educaci´on, esto traduce a descartar contenidos cuyos prerrequisitos conceptuales no hayan sido dominados por el estudiante. Su ventaja es el desacoplamiento total entre el entrenamiento del modelo neuronal y la evoluci´on del grafo: el cat´alogo de contenidos puede crecer o modificarse sin reentrenar la red. Su riesgo es la escasez de candidatos: si el modelo ignora sistem´aticamente la estructura pedag´ogica, el filtrado puede dejar al usuario con muy pocas recomendaciones v´alidas. 

2. **KG como enriquecimiento de embeddings:** Los embeddings del grafo (obtenidos mediante t´ecnicas como Node2Vec, DeepWalk o Graph Neural Networks) se inyectan como vectores adicionales de entrada en el modelo de recomendaci´on. De este modo, el modelo aprende impl´ıcitamente a respetar la estructura del grafo durante el entrenamiento. Su ventaja es que las restricciones pedag´ogicas se incorporan en la funci´on de predicci´on, reduciendo la probabilidad de generar candidatos inv´alidos. Su desventaja es el acoplamiento: cualquier cambio en el grafo requiere reentrenar o ajustar el modelo. 

3. **KG como camino de explicaci´on:** El grafo se utiliza para generar rutas de razo- 

13 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

namiento que expliquen por qu´e se recomienda un ´ıtem (por ejemplo: ”se recomienda ’Fondos indexados’ porque el usuario domin´o ’Diversificaci´on’, que es prerrequisito de ’Inversi´on’, que a su vez habilita ’Fondos indexados’”). Esta estrategia mejora la transparencia del sistema y fomenta la confianza del usuario, aspecto especialmente relevante en educaci´on financiera donde la comprensi´on del ”porqu´erefuerza el aprendizaje. 



<!-- Start of picture text -->
Perfil del usuario Modelo de Contenidos Recomendaciones<br>edad, nivel, intereses recomendaci´on candidatos finales<br>filtra por<br>prerrequisitos<br>Grafo de conocimiento<br>financiero<br>Ahorro Inter´es Riesgo Fondos<br>relaciones REQUIERE<br><!-- End of picture text -->

Figura 2.1: Uso de un grafo de conocimiento como post-filtro en un sistema de recomendaci´on educativo 

La Figura 2.1 muestra un ejemplo simplificado del uso de un grafo de conocimiento en un sistema de recomendaci´on educativo. El modelo genera una lista inicial de contenidos candidatos y el grafo act´ua como mecanismo de post-filtro, descartando aquellos contenidos cuyos prerrequisitos conceptuales no han sido dominados por el usuario. 

La alfabetizaci´on financiera es inherentemente jer´arquica: no se puede ense˜nar “fondos indexados” sin que el usuario domine previamente “diversificaci´on” e “inter´es compuesto”. Ignorar esta estructura genera recomendaciones t´ecnicamente precisas (alto NDCG@k) pero pedag´ogicamente in´utiles. El KG garantiza que el sistema respete el orden de adquisici´on del conocimiento, funcionando como capa de validaci´on sem´antica sobre el modelo de recomendaci´on. 

14 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

## **2.3. Machine Learning para Personalizaci´on del Aprendizaje** 

### **2.3.1. Educational Recommender Systems (ERS)** 

Los sistemas de recomendaci´on educativos constituyen una especializaci´on de los RecSys generalistas, donde el objetivo no es maximizar el clic o el tiempo de consumo, sino el aprendizaje efectivo. Esta l´ınea de investigaci´on ha experimentado un crecimiento significativo en los ´ultimos a˜nos debido al avance de t´ecnicas de Machine Learning aplicadas a la personalizaci´on educativa (Khanal, Prasad, Alsadoon, y Maag, 2020). 

Esto introduce m´etricas de evaluaci´on espec´ıficas: 

#### **Mastery Learning** 

#### **Retenci´on a largo plazo** 

#### **Engagement educativo** 

### **2.3.2. NLP para la categorizaci´on de contenido educativo** 

El cat´alogo de contenido financiero disponible carece de una taxonom´ıa unificada. El Procesamiento de Lenguaje Natural (NLP) permite: 

#### **Extracci´on autom´atica de t´opicos** 

#### **Vectorizaci´on sem´antica** 

Para este TFM, el NLP actuar´a como puente entre el contenido crudo y el espacio vectorial del modelo de recomendaci´on. 

## **2.4. Estado del arte en RecSys aplicados a educaci´on financiera** 

La aplicaci´on de sistemas de recomendaci´on al ´ambito de la educaci´on financiera es un campo incipiente, pero de creciente inter´es. A continuaci´on se analizan los trabajos m´as relevantes identificados en la literatura, ordenados seg´un su cercan´ıa t´ecnica con la propuesta del presente trabajo. 

15 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

### **2.4.1. Sistemas basados en grafos de conocimiento y deep learning** 

El trabajo m´as directamente comparable es el de Verma et al. (Verma y cols., 2023), quienes desarrollaron un sistema de recomendaci´on de art´ıculos educativos financieros para una multinacional de servicios financieros. Los autores combinan un _knowledge graph_ generado autom´aticamente a partir de datos estructurados, como demograf´ıa de suscriptores, temas y productos, y datos no estructurados, como el texto completo de art´ıculos educativos. 

Sobre esta representaci´on, proponen un recomendador basado en _reinforcement learning_ que recorre el grafo para encontrar rutas de recomendaci´on explicables. Los autores reportan un MAP@10 del 43,76 %, superando a baselines de filtrado colaborativo, como _Bayesian Personalized Ranking_ (BPR), y _Neural Collaborative Filtering_ (NCF). 

No obstante, su sistema no modela dependencias pedag´ogicas entre conceptos ni incorpora un mecanismo de evaluaci´on de maestr´ıa. Su objetivo principal es maximizar la lectura de art´ıculos, no garantizar una progresi´on did´actica. 

### **2.4.2. Sistemas tutoriales inteligentes multiagente** 

Mar´ın y Notargiacomo (Mar´ın y Notargiacomo, 2021) proponen _Stima_ , un sistema tutorial inteligente multiagente para educaci´on financiera. El sistema adquiere conocimiento de expertos y utiliza an´alisis sint´actico, l´exico y sem´antico para definir perfiles financieros de los estudiantes y recomendar est´andares de planificaci´on financiera personalizada. 

Aunque este trabajo aborda el perfilado del usuario, su arquitectura se basa en reglas y agentes conversacionales. Por tanto, no utiliza _deep learning_ ni modela secuencias de aprendizaje mediante estructuras de grafo. 

### **2.4.3. Aprendizaje autom´atico para la predicci´on de alfabetizaci´on financiera** 

Zhu (Zhu, 2024) propone un marco de _machine learning_ supervisado para predecir niveles de alfabetizaci´on financiera en poblaci´on joven a partir de datos sociodemogr´aficos y conductuales. El autor entrena y compara distintos algoritmos, como ´arbol de decisi´on, _Random Forest_ , LightGBM y SVM, sobre datos de encuesta. 

El trabajo tambi´en aplica an´alisis de ablaci´on para identificar las caracter´ısticas m´as predictivas, entre ellas edad, nivel educativo, ingresos y experiencia previa con productos financieros. Aunque no construye un sistema de recomendaci´on de contenidos, demuestra 

16 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

la viabilidad del _machine learning_ para el perfilado autom´atico de usuarios en el dominio financiero. Esta capacidad es relevante para mitigar el problema de _cold start_ en sistemas recomendadores educativos. 

### **2.4.4. Algoritmos de targeting con aprendizaje autom´atico** 

D’Ignazio y Buratti (D’Ignazio y Buratti, 2023) emplean t´ecnicas de _machine learning_ para identificar, a partir de caracter´ısticas observables, qu´e individuos podr´ıan beneficiarse m´as de programas de educaci´on financiera. 

Su aporte se centra en la personalizaci´on de la entrega de la formaci´on, no en la personalizaci´on del contenido educativo. En consecuencia, el trabajo no aborda la recomendaci´on de materiales, la secuenciaci´on pedag´ogica ni la adaptaci´on progresiva del aprendizaje. 

### **2.4.5. Sistemas recomendadores educativos con grafos de conocimiento** 

Fuera del ´ambito financiero, existe una l´ınea de investigaci´on activa sobre grafos de conocimiento aplicados a sistemas de recomendaci´on educativos. Hua et al. (Hua, Yang, y Ji, 2025) proponen KGCN-UP, un modelo basado en _Knowledge Graph Convolutional Networks_ con preferencias de usuario para la recomendaci´on de cursos MOOC. Este enfoque aborda, entre otros aspectos, el problema de la escasez de datos. 

De forma similar, Duan et al. (Duan y cols., 2025) presentan LKGA, una red de atenci´on sobre grafos de conocimiento orientada a mejorar la recomendaci´on de recursos de aprendizaje en sistemas de tutor´ıa inteligente. 

Estos trabajos demuestran la viabilidad t´ecnica de integrar grafos de conocimiento con modelos neuronales en contextos educativos. Sin embargo, no abordan la especificidad del dominio financiero ni el p´ublico de j´ovenes profesionales. 

### **2.4.6. Comparativa de trabajos relacionados** 

En la Tabla 2.1 se resume la comparativa t´ecnica entre los trabajos revisados y la propuesta del presente TFM. 

17 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

Tabla 2.1: Comparativa de trabajos relacionados en RecSys aplicados a educaci´on financiera y sistemas educativos con grafos de conocimiento 

|**Trabajo**|**Dominio**|**Modelo**|**KG**|**Cold start**|**Secuenciaci´on**<br>**pedag´ogica**|
|---|---|---|---|---|---|
|Verma<br>et<br>al.|Art´ıculos|RL + KG|S´ı|Limitado|No|
|(2023)|fnancieros<br>educativos|||||
|Mar´ın<br>y<br>Notar-|Planifcaci´on|Reglas multiagente|No|Perflado ma-|No|
|giacomo (2021)|fnanciera|||nual||
|Zhu (2024)|Alfabetizaci´on|ML<br>supervisado:|No|Con datos de|No|
||fnanciera<br>en|RF,<br>LightGBM,||encuesta||
||j´ovenes|SVM||||
|D’Ignazio y Bu-|Educaci´on<br>f-|ML cl´asico|No|No aplica|No|
|ratti (2023)|nanciera: _tar-_<br>_geting_|||||
|Hua et al. (2025)|Cursos<br>MOOC|KGCN-UP|S´ı|Parcial|No|
|Duan<br>et<br>al.|Tutor´ıa inteli-|LKGA: KG + aten-|S´ı|Parcial|No|
|(2025)|gente|ci´on||||
|**Propuesta**|**Educaci´on**|**Feature-aware**|**S´ı**|**S´ı, median-**|**S´ı, median-**|
||**fnanciera**|**NeuMF + KG**||**te**<br>**cues-**|**te grafo de**|
||**en j´ovenes**|||**tionario**|**prerrequi-**|
|||||**diagn´ostico**|**sitos**|



### **2.4.7. Vac´ıo identificado** 

Ninguno de los trabajos revisados combina _Neural Collaborative Filtering_ con grafos con grafos de conocimiento en el dominio espec´ıfico de la educaci´on financiera para j´ovenes, integrando simult´aneamente tres elementos: personalizaci´on de contenido mediante un modelo h´ıbrido de _deep learning_ , restricciones pedag´ogicas de secuenciaci´on modeladas expl´ıcitamente mediante un grafo de conocimiento y un mecanismo de evaluaci´on de maestr´ıa que retroalimente el sistema. 

Este vac´ıo constituye la contribuci´on cient´ıfica principal del presente trabajo. La propuesta plantea un sistema basado en _feature-aware NeuMF_ combinado con un grafo de conoci- 

18 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

miento que act´ua como mecanismo de control pedag´ogico, evitando recomendaciones que no respeten los prerrequisitos conceptuales del usuario. 

## **2.5. Selecci´on de arquitectura y justificaci´on del stack tecnol´ogico** 

Tras el an´alisis del estado del arte, se procede a justificar la arquitectura y el stack tecnol´ogico seleccionados para el prototipo. La propuesta se basa en la integraci´on de un modelo de recomendaci´on, un grafo de conocimiento y una aplicaci´on web conectada mediante API, en l´ınea con el objetivo de desarrollar una prueba de concepto funcional. 

## **2.6. Selecci´on de arquitectura y justificaci´on del stack tecnol´ogico** 

### **2.6.1. Modelo de recomendaci´on: NeuMF** 

La elecci´on de una arquitectura basada en NeuMF frente a alternativas cl´asicas, como la factorizaci´on matricial o los sistemas basados en contenido, se fundamenta en tres argumentos principales. 

En primer lugar, se considera el problema del _cold start_ pedag´ogico. Los usuarios nuevos no tienen historial de interacci´on con la plataforma, por lo que un sistema puramente colaborativo no puede funcionar adecuadamente desde el primer uso. Para mitigar esta limitaci´on, se propone una variante _feature-aware NeuMF_ , que integra caracter´ısticas del usuario, como edad, ingresos, conocimientos previos y perfil de riesgo, en el vector de entrada del MLP. Esto permite inferir preferencias iniciales incluso sin historial de interacci´on. En segundo lugar, la educaci´on financiera presenta una alta heterogeneidad en los perfiles de usuario. Las finanzas personales dependen de relaciones no lineales entre variables como ingresos, edad, conocimientos previos, h´abitos de ahorro y propensi´on al riesgo. Estas relaciones no son capturadas de forma suficiente por modelos lineales de factorizaci´on matricial. En cambio, el componente MLP de NeuMF permite modelar interacciones m´as complejas entre variables contextuales. 

En tercer lugar, la arquitectura GMF+MLP ofrece modularidad. Permite experimentar con distintas configuraciones, como solo GMF, solo MLP, combinaci´on completa o variantes con y sin _features_ contextuales. Esta flexibilidad facilita comparar emp´ıricamente qu´e 

19 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

configuraci´on funciona mejor en el dominio educativo. 

La selecci´on definitiva del modelo no se plantea como una decisi´on exclusivamente te´orica. Se sustentar´a en una evaluaci´on experimental en la que se medir´an m´etricas est´andar de recomendaci´on, como NDCG@k y Precision@k, junto con una m´etrica espec´ıfica de coherencia pedag´ogica. Esta m´etrica se define como el porcentaje de recomendaciones que respetan las dependencias conceptuales del dominio. 

### **2.6.2. Grafo de conocimiento: Neo4j** 

Se selecciona Neo4j como base de datos orientada a grafos. Esta elecci´on se justifica por tres motivos: la naturaleza pedag´ogica del dominio, la comparaci´on frente a bases de datos relacionales y la comparaci´on frente a otras bases de datos de grafos. 

#### **Naturaleza del dominio** 

La educaci´on financiera presenta una estructura conceptual jer´arquica. Los conceptos no existen de forma aislada, sino conectados mediante relaciones de prerrequisito, especializaci´on y secuencia. Por ejemplo, antes de estudiar fondos indexados, el usuario deber´ıa comprender conceptos como riesgo, diversificaci´on, inflaci´on e inter´es compuesto. 

Modelar estas relaciones en una base de datos relacional requerir´ıa tablas intermedias y consultas recursivas para recuperar todos los prerrequisitos de un contenido. En cambio, en un grafo esta consulta puede resolverse mediante recorridos entre nodos y relaciones, lo que resulta m´as natural para representar dependencias conceptuales. 

#### **Comparativa frente a bases relacionales** 

En bases de datos relacionales, como PostgreSQL o MySQL, la validaci´on de dependencias pedag´ogicas implicar´ıa consultas recursivas o uniones sucesivas entre tablas. Esto puede aumentar la complejidad de consulta y dificultar el mantenimiento del modelo cuando crece el n´umero de conceptos y relaciones. 

Neo4j almacena las relaciones como parte central del modelo de datos, lo que facilita recorrer conexiones entre conceptos y contenidos. Esto resulta adecuado para validar, antes de mostrar una recomendaci´on, si el usuario ha cubierto los prerrequisitos necesarios. 

20 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

#### **Comparativa frente a otras bases de grafos** 

Tambi´en se consideraron alternativas como ArangoDB, Amazon Neptune y JanusGraph. Sin embargo, se descartaron por las siguientes razones: 

- **ArangoDB:** aunque es una base de datos multimodelo y soporta grafos, Neo4j ofrece un ecosistema m´as consolidado para consultas de grafos y recorridos complejos mediante Cypher. 

- **Amazon Neptune:** requiere infraestructura en AWS, lo que incrementa la complejidad de despliegue y puede generar costes recurrentes. Para un prototipo acad´emico, esta dependencia no resulta necesaria. 

- **JanusGraph:** est´a orientada a grafos masivos distribuidos con backends como Cassandra o HBase. Su arquitectura excede las necesidades del presente TFM, donde el grafo de conocimiento financiero ser´a de tama˜no moderado. 

#### **Factores decisivos a favor de Neo4j** 

Los factores decisivos para seleccionar Neo4j son los siguientes: 

- **Lenguaje Cypher:** permite expresar consultas de grafos de forma declarativa y legible. Por ejemplo, consultar qu´e contenidos son accesibles para un usuario seg´un los conceptos que ya domina. 

- **Ecosistema Python:** el driver oficial de Neo4j y bibliotecas como `py2neo` facilitan la integraci´on con el backend y el pipeline de datos. 

- **Community Edition:** permite ejecutar el prototipo sin licencias comerciales ni dependencia de proveedores cloud. 

- **Modelo de grafo con propiedades:** permite almacenar atributos en nodos y relaciones. Por ejemplo, un nodo `Concepto` puede tener propiedades como `nombre` , `dificultad` y `categoria` ; una relaci´on `REQUIERE` puede incluir `peso` ~~`p`~~ `edagogico` o `tipo dependencia` . 

### **2.6.3. Motor de IA y backend** 

Para el entrenamiento y servido del modelo NeuMF se selecciona PyTorch. Esta biblioteca ofrece flexibilidad para definir arquitecturas personalizadas y facilita la experimentaci´on con variantes del modelo, incluyendo configuraciones con variables contextuales. 

Para la exposici´on del modelo mediante API REST se selecciona FastAPI. Esta tecnolog´ıa 

21 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

permite construir servicios web de forma eficiente, incorpora tipado mediante Pydantic y genera autom´aticamente documentaci´on OpenAPI. Esto facilita la integraci´on con el frontend y las pruebas del prototipo. 

### **2.6.4. Integraci´on KG-RecSys: estrategia de post-filtro** 

Respecto a la integraci´on entre el grafo de conocimiento y el sistema de recomendaci´on, se adopta como estrategia inicial un enfoque de post-filtro. En esta configuraci´on, el modelo NeuMF genera un ranking de contenidos candidatos y el grafo de conocimiento descarta aquellos que violan prerrequisitos conceptuales. 

Esta estrategia se prefiere inicialmente porque desacopla el entrenamiento del modelo neuronal de la evoluci´on del grafo de conocimiento. De este modo, el cat´alogo de contenidos puede crecer o modificarse sin necesidad de reentrenar inmediatamente la red. 

No obstante, como l´ınea de comparaci´on, se contempla evaluar una estrategia alternativa basada en el enriquecimiento de embeddings con informaci´on del grafo. Esto permitir´a analizar si una integraci´on m´as profunda entre el modelo de recomendaci´on y el grafo mejora la calidad de las recomendaciones. 

## **2.7. Conclusiones del estado del arte** 

La revisi´on de la literatura presentada en este cap´ıtulo permite extraer las siguientes conclusiones orientadoras para el desarrollo del trabajo: 

1. **La alfabetizaci´on financiera de j´ovenes espa˜noles presenta una brecha relevante.** Existe una diferencia entre la capacidad de ahorro declarada y la gesti´on financiera efectiva, especialmente en el uso de instrumentos de planificaci´on e inversi´on. Esta situaci´on puede verse agravada por sesgos cognitivos como la sobreconfianza, el sesgo de presente o el efecto de anclaje. 

2. **Los sistemas de recomendaci´on tradicionales son insuficientes para el contexto educativo.** El filtrado colaborativo y los sistemas basados en contenido pueden ser ´utiles como l´ıneas base, pero no modelan adecuadamente relaciones pedag´ogicas, prerrequisitos conceptuales ni progresi´on de aprendizaje. 

3. **NeuMF representa una alternativa adecuada para la personalizaci´on.** Su arquitectura combina la capacidad de GMF para capturar patrones de interacci´on con la flexibilidad del MLP para modelar relaciones no lineales. Adem´as, una variante 

22 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

_feature-aware_ permite incorporar informaci´on contextual del usuario. 

4. **Los grafos de conocimiento aportan estructura pedag´ogica.** Los modelos de recomendaci´on puros tienden a priorizar relevancia o probabilidad de interacci´on. En cambio, un grafo de conocimiento permite representar conceptos, prerrequisitos y rutas de aprendizaje. 

5. **Existe un vac´ıo cient´ıfico identificado.** No se ha identificado en la literatura revisada un sistema que combine Neural Collaborative Filtering con Knowledge Graphs espec´ıficamente dise˜nado para la educaci´on financiera de j´ovenes profesionales, integrando simult´aneamente personalizaci´on de contenido, restricciones pedag´ogicas y evaluaci´on de maestr´ıa. Este vac´ıo constituye la oportunidad de contribuci´on del presente trabajo. 

23 

# **3. Objetivos y metodolog´ıa de trabajo** 

## **3.1. Objetivos del trabajo** 

El objetivo general del presente trabajo es desarrollar un prototipo funcional de una plataforma software basada en inteligencia artificial que, mediante t´ecnicas de aprendizaje autom´atico y sistemas de recomendaci´on, permita personalizar contenidos de educaci´on financiera en funci´on del perfil y del contexto econ´omico del usuario, con especial enfoque en j´ovenes profesionales. 

Como objetivos espec´ıficos se plantean: 

- Dise˜nar un modelo de perfilado financiero mediante la recopilaci´on, procesamiento y an´alisis de datos econ´omicos, demogr´aficos y comportamentales del usuario. 

- Seleccionar modelos de aprendizaje autom´atico, optimizar sus hiperpar´ametros y evaluar su desempe˜no en tareas de segmentaci´on y clasificaci´on de perfiles financieros. Desarrollar e implementar un prototipo web basado en inteligencia artificial que integre el modelo de perfilado financiero y un sistema de recomendaci´on de contenidos educativos personalizados, con el fin de validar su funcionamiento en un entorno simulado o real. 

El impacto esperado del trabajo es doble. Desde el punto de vista acad´emico, permitir´a la aplicaci´on pr´actica de conocimientos en aprendizaje autom´atico, sistemas de recomendaci´on y desarrollo de software. Desde una perspectiva social, la personalizaci´on de la educaci´on financiera en j´ovenes profesionales contribuye a reducir las barreras de acceso al conocimiento econ´omico, favoreciendo una formaci´on m´as equitativa y adaptada a las necesidades individuales. Asimismo, este enfoque se alinea con los Objetivos de Desarrollo Sostenible, en particular con el ODS 4 (Educaci´on de calidad) y el ODS 10 (Reducci´on de las desigualdades). 

24 

# **4. Identificaci´on de Requisitos** 

## **4.1. Introducci´on** 

En este cap´ıtulo se identifican los requisitos principales del prototipo. El objetivo es definir qu´e debe hacer el sistema, qu´e datos necesita y qu´e restricciones debe cumplir para recomendar contenidos educativos de educaci´on financiera de forma personalizada. El sistema est´a dirigido a j´ovenes residentes en Espa˜na, entre 18 y 34 a˜nos, con inter´es en mejorar su alfabetizaci´on financiera. La plataforma no pretende ofrecer asesoramiento financiero, sino recomendar contenidos educativos adecuados al nivel y progreso del usuario. 

## **4.2. Identificaci´on del problema** 

La educaci´on financiera es importante para tomar decisiones econ´omicas responsables. Sin embargo, muchos recursos disponibles ofrecen contenidos gen´ericos que no consideran el nivel de conocimiento, el contexto econ´omico ni las necesidades concretas de cada usuario. En este trabajo, el problema se centra en la falta de personalizaci´on en los contenidos de educaci´on financiera. Un mismo contenido no es igual de ´util para un usuario principiante que para otro con conocimientos previos. Por ello, se propone un sistema capaz de recomendar contenidos seg´un el perfil del usuario y su progreso de aprendizaje. 

Adem´as, en educaci´on financiera es necesario evitar recomendaciones demasiado avanzadas. Por ejemplo, no ser´ıa adecuado recomendar contenidos sobre inversi´on si el usuario no comprende antes conceptos b´asicos como ahorro, inter´es, riesgo o diversificaci´on. 

## **4.3. Usuario objetivo** 

El usuario objetivo del sistema son j´ovenes residentes en Espa˜na, entre 18 y 34 a˜nos. Este grupo puede incluir estudiantes, j´ovenes profesionales o personas que empiezan a gestionar ingresos, ahorro, deuda o inversi´on b´asica. 

25 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

#### Tabla 4.1: Perfil del usuario objetivo 

**Aspecto Descripci´on** Edad 18 a 34 a˜nos. Ubicaci´on Espa˜na. Nivel financiero B´asico o intermedio. Necesidad principal Aprender finanzas personales de forma progresiva. Uso esperado Plataforma web de recomendaci´on educativa. 

## **4.4. Contexto de uso** 

El sistema se utilizar´a como una aplicaci´on web. El usuario completar´a un cuestionario inicial para definir su perfil financiero y, a partir de esa informaci´on, recibir´a recomendaciones de contenidos educativos. 

El uso esperado ser´a progresivo. El usuario podr´a empezar con temas b´asicos, como presupuesto, ahorro o deuda, y avanzar hacia temas m´as complejos, como inversi´on, diversificaci´on o planificaci´on financiera. 

## **4.5. Requisitos funcionales** 

Los requisitos funcionales principales son: 

El sistema debe permitir identificar al usuario. 

- El sistema debe recoger informaci´on inicial mediante un cuestionario. 

- El sistema debe estimar el nivel financiero inicial del usuario. El sistema debe almacenar contenidos educativos clasificados por tema y dificultad. El sistema debe generar recomendaciones personalizadas. 

- El sistema debe evitar recomendar contenidos cuyos prerrequisitos no est´en cubiertos. El sistema debe registrar el progreso del usuario. 

- El sistema debe actualizar las recomendaciones seg´un la evoluci´on del usuario. El sistema debe mostrar una explicaci´on breve de cada recomendaci´on. 

## **4.6. Requisitos no funcionales** 

Los requisitos no funcionales principales son: 

26 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

- La aplicaci´on debe poder utilizarse desde un navegador web. 

- La interfaz debe ser clara y sencilla. 

- El sistema debe responder en tiempos aceptables. 

- Los datos personales del usuario deben protegerse adecuadamente. 

- El sistema debe ser modular para permitir mejoras futuras. 

- El cat´alogo de contenidos debe poder ampliarse sin modificar todo el sistema. 

## **4.7. Requisitos de datos** 

El sistema necesita distintos tipos de datos para funcionar correctamente: 

- **Datos del usuario:** edad, nivel educativo, situaci´on laboral, conocimientos financieros iniciales, h´abitos de ahorro y experiencia previa. 

- **Datos de contenidos:** t´ıtulo, descripci´on, tema, nivel de dificultad, duraci´on, formato y fuente. 

- **Datos conceptuales:** conceptos financieros y relaciones de prerrequisito. 

- **Datos de interacci´on:** contenidos vistos, completados, valoraciones y resultados de cuestionarios. 

Estos datos permiten relacionar el perfil del usuario con los contenidos disponibles y con su progreso de aprendizaje. 

## **4.8. Requisitos pedag´ogicos** 

Dado que el objetivo del sistema es educativo, las recomendaciones deben seguir una 

progresi´on l´ogica. Por ello, se establecen los siguientes requisitos pedag´ogicos: 

- Los contenidos deben organizarse por nivel de dificultad. 

- Cada contenido debe indicar qu´e conceptos ense˜na. 

- Cada contenido debe indicar qu´e conceptos requiere previamente. 

- El sistema debe priorizar contenidos adecuados al nivel del usuario. 

- El sistema debe evitar contenidos demasiado complejos para usuarios principiantes. 

- Las recomendaciones deben favorecer el aprendizaje, no solo la interacci´on. 

27 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

## **4.9. Requisitos de seguridad financiera** 

El sistema debe limitarse a la educaci´on financiera. Por tanto, se definen las siguientes restricciones: 

- El sistema no debe recomendar productos financieros concretos. 

- El sistema no debe dar asesoramiento financiero personalizado. 

- Los contenidos de inversi´on solo deben recomendarse si el usuario domina conceptos previos. 

- Las fuentes de contenido deben ser confiables, preferentemente institucionales. 

- El sistema debe diferenciar claramente entre educaci´on financiera y consejo financiero. 

## **4.10. Requisitos del sistema de recomendaci´on** 

El recomendador debe generar una lista de contenidos adecuados para cada usuario. Para ello, debe considerar: 

el perfil inicial del usuario; 

- su nivel de conocimiento financiero; 

- sus intereses u objetivos de aprendizaje; 

- los contenidos disponibles; 

- los prerrequisitos conceptuales de cada contenido; 

el progreso registrado en la plataforma. 

El ranking generado por el modelo de recomendaci´on deber´a filtrarse mediante reglas pedag´ogicas. De esta forma, el sistema evitar´a mostrar contenidos que el usuario a´un no est´a preparado para comprender. 

## **4.11. Requisitos del grafo de conocimiento** 

El grafo de conocimiento representar´a los conceptos financieros y sus relaciones. Su funci´on 

principal ser´a comprobar si un usuario cumple los prerrequisitos necesarios antes de recibir una recomendaci´on. 

El grafo deber´a permitir representar: 

conceptos financieros; 

28 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

contenidos educativos; 

- relaciones de prerrequisito entre conceptos; 

- conceptos ense˜nados por cada contenido; 

conceptos ya dominados por el usuario. 

Por ejemplo, antes de recomendar un contenido sobre fondos indexados, el sistema deber´ıa comprobar si el usuario entiende conceptos como riesgo, diversificaci´on, inflaci´on e inter´es compuesto. 

## **4.12. Conclusiones del cap´ıtulo** 

En este cap´ıtulo se definieron los requisitos principales del prototipo. Estos requisitos muestran que el sistema no debe limitarse a recomendar contenidos relevantes, sino que debe hacerlo de forma adecuada al nivel del usuario, respetando una progresi´on pedag´ogica y evitando recomendaciones financieras inadecuadas. 

Los requisitos identificados servir´an como base para el dise˜no de la arquitectura, la selecci´on 

tecnol´ogica y la implementaci´on del prototipo. 

29 

# **5. Descripci´on de la herramienta software desarrollada** 

## **5.1. Descripci´on** 

La herramienta desarrollada consiste en un prototipo web para la recomendaci´on personalizada de contenidos educativos en educaci´on financiera. El sistema permite que el usuario introduzca informaci´on b´asica sobre su perfil, reciba recomendaciones adaptadas a su nivel y consulte contenidos organizados seg´un una progresi´on pedag´ogica. 

El prototipo se plantea como una prueba de concepto funcional. Su objetivo no es desplegar una plataforma productiva, sino demostrar la viabilidad t´ecnica del enfoque propuesto mediante la integraci´on de un modelo de recomendaci´on, una API y una aplicaci´on web. 

### **5.1.1. Objetivo de la herramienta** 

El objetivo principal de la herramienta es recomendar contenidos educativos personalizados a j´ovenes residentes en Espa˜na, considerando su nivel de conocimiento financiero, sus intereses y los prerrequisitos conceptuales de cada contenido. 

La aplicaci´on no recomienda productos financieros ni ofrece asesoramiento financiero personalizado. Su funci´on se limita a organizar y recomendar recursos educativos de forma progresiva. 

### **5.1.2. Proceso de desarrollo** 

El desarrollo del prototipo se organiz´o en fases incrementales. Cada fase permiti´o construir una parte concreta del sistema hasta obtener una versi´on funcional. 

30 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

Tabla 5.1: Fases del proceso de desarrollo 

|**Fase**|**Descripci´on**|
|---|---|
|Fase 1|Defnici´on de requisitos del sistema y del perfl de usuario<br>objetivo.|
|Fase 2|Construcci´on del cat´alogo inicial de contenidos educativos.|
|Fase 3|Defnici´on de conceptos fnancieros y relaciones de prerre-<br>quisito.|
|Fase 4|Implementaci´on del backend y de la API de recomendaci´on.|
|Fase 5|Desarrollo de la interfaz web del usuario.|
|Fase 6|Integraci´on del sistema de recomendaci´on con el grafo de<br>conocimiento.|
|Fase 7|Pruebas funcionales del prototipo.|



### **5.1.3. Arquitectura general** 

La arquitectura del sistema se compone de cuatro bloques principales: interfaz web, backend, motor de recomendaci´on y grafo de conocimiento. La interfaz permite la interacci´on con el usuario; el backend coordina las peticiones; el modelo genera recomendaciones; y el grafo valida que los contenidos respeten los prerrequisitos pedag´ogicos. 

Nota pendiente Incluir diagrama de arquitectura general. 

El flujo general del sistema es el siguiente: 

1. El usuario accede a la aplicaci´on web. 

2. Completa un cuestionario inicial de perfilado. 

3. El backend procesa los datos del usuario. 

4. El modelo de recomendaci´on genera una lista de contenidos candidatos. 

5. El grafo de conocimiento filtra los contenidos que no cumplen los prerrequisitos. 

6. La aplicaci´on muestra las recomendaciones finales. 

31 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

### **5.1.4. Componentes principales** 

El prototipo est´a formado por los siguientes componentes: 

- **Frontend web:** permite completar el cuestionario inicial, visualizar recomendaciones y consultar contenidos. 

- **Backend:** expone la API del sistema y coordina la comunicaci´on entre los componentes. 

- **Modelo de recomendaci´on:** genera un ranking personalizado de contenidos educativos. 

- **Grafo de conocimiento:** representa conceptos financieros, contenidos y relaciones de prerrequisito. 

- **Base de datos:** almacena usuarios, contenidos, interacciones y resultados de aprendizaje. 

### **5.1.5. Tecnolog´ıas utilizadas** 

El prototipo utiliza un stack tecnol´ogico orientado al desarrollo r´apido de una aplicaci´on demostrable. Se emplea Python para el procesamiento de datos, PyTorch para el modelo de recomendaci´on, FastAPI para la integraci´on mediante API, Neo4j para el grafo de conocimiento y React para la interfaz web. 

Tabla 5.2: Tecnolog´ıas utilizadas en el prototipo 

|**Tecnolog´ıa**|**Uso en el sistema**|
|---|---|
|Python|Procesamiento de datos y l´ogica principal.|
|PyTorch|Implementaci´on del modelo de recomendaci´on.|
|FastAPI|Desarrollo de la API de integraci´on.|
|Neo4j|Representaci´on del grafo de conocimiento fnanciero.|
|React|Desarrollo de la interfaz web del usuario.|
|Pandas / NumPy|Limpieza, transformaci´on y an´alisis de datos.|



### **5.1.6. Funcionamiento de la aplicaci´on** 

Desde el punto de vista del usuario, el funcionamiento de la herramienta se organiza en cuatro pasos: 

32 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

1. **Perfilado inicial:** el usuario responde un cuestionario sobre conocimientos financieros, h´abitos e intereses. 

2. **Generaci´on de recomendaciones:** el sistema calcula contenidos adecuados para el perfil del usuario. 

3. **Filtrado pedag´ogico:** el grafo elimina contenidos cuyos prerrequisitos no est´en cubiertos. 

4. **Visualizaci´on de resultados:** el usuario recibe una lista de contenidos recomendados y puede consultar su progreso. 

Nota pendiente 

Incluir diagrama flujo de interaccion, captura de las pantallas principales, link al repo 

### **5.1.7. Pantallas principales** 

A continuaci´on se presentan las pantallas principales del prototipo. Estas capturas permi- 

ten entender el funcionamiento general de la aplicaci´on. 

#### **Pantalla de inicio** 

La pantalla de inicio presenta el objetivo de la plataforma y permite iniciar el proceso de perfilado. 

#### **Cuestionario inicial** 

El cuestionario inicial recopila informaci´on b´asica sobre el usuario, como nivel de conoci- 

miento financiero, experiencia previa e intereses de aprendizaje. 

#### **Pantalla de recomendaciones** 

Esta pantalla muestra los contenidos educativos recomendados. Cada recomendaci´on pue- 

de incluir el t´ıtulo, tema, dificultad y una breve explicaci´on del motivo por el que fue seleccionada. 

#### **Pantalla de progreso** 

La pantalla de progreso permite visualizar los contenidos completados y el avance del usuario dentro del itinerario educativo. 

33 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

### **5.1.8. Integraci´on de los componentes** 

La integraci´on del prototipo se realiza mediante una API que conecta la aplicaci´on web con el backend y el modelo de recomendaci´on. Esta API recibe los datos del usuario, solicita recomendaciones al modelo, consulta el grafo de conocimiento y devuelve al frontend una lista final de contenidos recomendados. 

### **5.1.9. Resultado obtenido** 

### **5.1.10. Conclusi´on** 

34 

# **6. Conclusiones Futuro y Trabajo** 

En la Ecuaci´on (6.1) 



En la siguiente Tabla 6.1 



Tabla 6.1: Tabla 1 

En la siguiente Figura 6.1 



Figura 6.1: Logo Unir 

(Pimentel y Teixeira, 2016) (da S. Bessa, da Silva, Frederico, y Ricarte, 2023) 

## **Referencias** 

- da S. Bessa, J., da Silva, J. V., Frederico, M. N., y Ricarte, G. C. (2023, sep). Sharp hessian estimates for fully nonlinear elliptic equations under relaxed convexity assumptions, oblique boundary conditions and applications. _Journal of Differential Equations_ , _367_ , 451-493. Descargado de `https://doi.org/10.1016%2Fj.jde.2023.05.006` doi: 10.1016/j.jde.2023.05.006 

- D’Ignazio, A., y Buratti, G. (2023). Improving the effectiveness of financial education programs: A targeting approach. _Journal of Consumer Affairs_ . Descargado de `https://doi.org/10.1111/joca.12577` (Tambi´en disponible como Bank of Italy Occasional Paper No. 765) doi: 10.1111/joca.12577 

- Duan, C., Yang, J., Cui, Q., Zhang, W., Wan, X., y Zhang, M. (2025). Enhancing the recommendation of learning resources for learners via an advanced knowledge 

35 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

graph. _Applied Sciences_ , _15_ (8), 4204. Descargado de `https://doi.org/10.3390/ app15084204` doi: 10.3390/app15084204 

- Gao, Y., Li, Y.-F., Lin, Y., Gao, H., y Khan, L. (2020). Deep learning on knowledge graph for recommender system: A survey. _arXiv preprint arXiv:2004.00387_ . 

- Guo, Q., Zhuang, F., Qin, C., Zhu, H., Xie, X., Xiong, H., y He, Q. (2020). A survey on knowledge graph-based recommender systems. _IEEE Transactions on Knowledge and Data Engineering_ . doi: 10.1109/TKDE.2020.3028705 

- He, X., Liao, L., Zhang, H., Nie, L., Hu, X., y Chua, T.-S. (2017a). Neural collaborative filtering. _Proceedings of the 26th International Conference on World Wide Web_ , 173–182. 

- He, X., Liao, L., Zhang, H., Nie, L., Hu, X., y Chua, T.-S. (2017b, apr). Neural collaborative filtering. En _Proceedings of the 26th international conference on world wide web (www ’17)_ (pp. 173–182). Perth, Australia: ACM. Descargado de `http://dx.doi.org/ 10.1145/3038912.3052569` doi: 10.1145/3038912.3052569 

- Hospido, L., Machelett, M., Pidkuyko, M., y Villanueva, E. (2023, nov). _Encuesta de competencias financieras (ecf) 2021: Principales resultados y cambios desde 2016_ (Inf. T´ec.). Banco de Espa˜na. Descargado de `https://doi.org/10.53479/34752` doi: 10.53479/34752 

- Hua, Z., Yang, J., y Ji, W. (2025). Knowledge graph convolutional networks with user preferences for course recommendation. _Scientific Reports_ , _15_ , 30256. Descargado de `https://doi.org/10.1038/s41598-025-14150-5` doi: 10.1038/s41598-025-14150 -5 

- Khanal, S. S., Prasad, P., Alsadoon, A., y Maag, A. (2020). A systematic review: machine learning based recommendation systems for e-learning. _Education and Information Technologies_ , _25_ , 2635–2664. doi: 10.1007/s10639-019-10063-9 

- Lusardi, A., y Mitchell, O. S. (2014). The economic importance of financial literacy: Theory and evidence. _Journal of Economic Literature_ , _52_ (1), 5–44. Descargado de `https://doi.org/10.1257/jel.52.1.5` doi: 10.1257/jel.52.1.5 

- Mar´ın, R., y Notargiacomo, P. (2021). Multiagent intelligent tutoring system for financial literacy. _International Journal of Web-Based Learning and Teaching Technologies_ , _17_ (7), 1–13. Descargado de `https://doi.org/10.4018/IJWLTT.288035` doi: 10 .4018/IJWLTT.288035 

- Organisation for Economic Co-operation and Development. (2023). _OECD/INFE 2023_ 

36 

Mar´ıa Ver´onica Rodr´ıguez Mill´an Joaqu´ın Leandro Ram´ırez Huam´an M´aster en Inteligencia Artificial 

_International Survey of Adult Financial Literacy_ (Inf. T´ec.). Paris: OECD Publishing. Descargado de `https://www.oecd.org/finance/financial-education/ oecd-infe-2023-international-survey-of-adult-financial-literacy.htm` 

- Pimentel, E. A., y Teixeira, E. V. (2016). Sharp hessian integrability estimates for nonlinear elliptic equations: An asymptotic approach. _Journal de Math´ematiques Pures et Appliqu´ees_ , _106_ (4), 744-767. Descargado de `https://www.sciencedirect.com/ science/article/pii/S0021782416300101` doi: https://doi.org/10.1016/j.matpur .2016.03.010 

- Verma, G., Sarkar, S., Pillai, D., Chen, H., McCrae, J. P., Perge, J. A., . . . Buitelaar, P. (2023). _Empowering recommender systems using automatically generated knowledge graphs and reinforcement learning._ Descargado de `https://doi.org/10.48550/ arXiv.2307.04996` doi: 10.48550/arXiv.2307.04996 

- Zhang, S., Yao, L., Sun, A., y Tay, Y. (2019). Deep learning based recommender system: A survey and new perspectives. _ACM Computing Surveys_ , _52_ (1), 1–38. doi: 10.1145/ 3285029 

- Zhu, A. Y. F. (2024). Unlocking financial literacy with machine learning: A critical step to advance personal finance research and practice. _Technology in Society_ , _81_ , 102797. Descargado de `https://doi.org/10.1016/j.techsoc.2024.102797` doi: 10.1016/j.techsoc.2024.102797 

37 

# **A. Apendices** 

38 


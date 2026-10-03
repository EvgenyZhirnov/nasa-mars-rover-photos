"""Curated NASA Library searches, not a claim of complete telescope archives."""
GROUPS = [
    {'id': 'solar', 'title': 'Солнечная система', 'description': 'Восемь планет, Луна, Солнце и далёкий Плутон.'},
    {'id': 'space', 'title': 'Космические телескопы', 'description': 'Галактики, туманности и звёздные скопления в разных диапазонах света.'},
    {'id': 'ground', 'title': 'Наземные обсерватории', 'description': 'Материалы и совместные наблюдения, опубликованные в медиатеке NASA.'},
    {'id': 'deep', 'title': 'Дальний космос', 'description': 'Места, до которых свет путешествует тысячи и миллионы лет.'},
]
COLLECTIONS = [
    {'id':'moon','group':'solar','title':'Луна','query':'Moon surface','note':'Поверхность Луны, кратеры и снимки лунных миссий.'},
    {'id':'mercury','group':'solar','title':'Меркурий','query':'Mercury','params':{'title':'Mercury','center':'JPL'},'note':'Поверхность и наблюдения ближайшей к Солнцу планеты.'},
    {'id':'venus','group':'solar','title':'Венера','query':'Venus','params':{'title':'Venus','center':'JPL'},'note':'Облака и поверхность Венеры. Часть изображений получена радаром и обработана в условных цветах.'},
    {'id':'earth','group':'solar','title':'Земля','query':'Earth Blue Marble','note':'Наша планета целиком — съёмка и мозаики спутниковых наблюдений.'},
    {'id':'mars','group':'solar','title':'Марс','query':'Mars planet','note':'Марс с орбиты и издалека. Снимки с поверхности — также в разделе «Марс».'},
    {'id':'jupiter','group':'solar','title':'Юпитер','query':'Jupiter','params':{'title':'Jupiter','center':'JPL'},'note':'Облака, вихри, полярные области и наблюдения Юпитера.'},
    {'id':'saturn','group':'solar','title':'Сатурн','query':'Saturn rings','note':'Планета, кольца и детали их структуры.'},
    {'id':'uranus','group':'solar','title':'Уран','query':'Uranus planet','note':'Снимки Voyager и наблюдения ледяного гиганта телескопами.'},
    {'id':'neptune','group':'solar','title':'Нептун','query':'Neptune','params':{'title':'Neptune','center':'JPL'},'note':'Далёкий ледяной гигант, его атмосфера и кольца.'},
    {'id':'sun','group':'solar','title':'Солнце','query':'Sun SDO','note':'Солнечная атмосфера в разных диапазонах. Цвета часто назначены при обработке.'},
    {'id':'pluto','group':'solar','title':'Плутон','query':'Pluto New Horizons','note':'Карликовая планета и наблюдения миссии New Horizons.'},
    {'id':'webb','group':'space','title':'James Webb','query':'Webb galaxy','note':'Инфракрасные наблюдения галактик, включая совместные результаты с другими телескопами.'},
    {'id':'hubble','group':'space','title':'Hubble','query':'Hubble nebula','note':'Туманности и звёздные облака глазами Hubble.'},
    {'id':'chandra','group':'space','title':'Chandra','query':'Chandra galaxy','note':'Рентгеновские наблюдения галактик и многоволновые композиции.'},
    {'id':'spitzer','group':'space','title':'Spitzer','query':'Spitzer nebula','note':'Инфракрасные снимки туманностей и межзвёздной пыли.'},
    {'id':'herschel','group':'space','title':'Herschel','query':'Herschel nebula','note':'Холодная пыль и туманности; материалы ESA/NASA и совместные наблюдения.'},
    {'id':'galex','group':'space','title':'GALEX','query':'GALEX galaxy','note':'Ультрафиолетовые наблюдения галактик.'},
    {'id':'vlt','group':'ground','title':'VLT / ESO','query':'Very Large Telescope','note':'Наблюдения и совместные работы с VLT из медиатеки NASA; не полный архив ESO.'},
    {'id':'keck','group':'ground','title':'Keck','query':'Keck galaxy','note':'Галактики и результаты совместных наблюдений с Keck. Некоторые изображения получены другими телескопами в рамках той же работы.'},
    {'id':'alma','group':'ground','title':'ALMA','query':'ALMA galaxy','note':'Небольшая подборка материалов о наблюдениях галактик с ALMA. Не полный архив обсерватории.'},
    {'id':'galaxies','group':'deep','title':'Галактики','query':'galaxy Hubble','note':'Спиральные, эллиптические и взаимодействующие галактики.'},
    {'id':'nebulae','group':'deep','title':'Туманности','query':'nebula','note':'Облака межзвёздного газа и пыли.'},
    {'id':'clusters','group':'deep','title':'Звёздные скопления','query':'globular cluster Hubble','note':'Тысячи звёзд в одном кадре.'},
    {'id':'supernovae','group':'deep','title':'Остатки сверхновых','query':'supernova remnant','note':'Наблюдения последствий звёздных взрывов.'},
]
BY_ID = {c['id']: c for c in COLLECTIONS}

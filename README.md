
# SuperRes

Инструмент разработанный для улучшения качества видео и генерации субтитров.
В нем используется алгоритм генеративно-состязательной сети и Deepgram API для субтитров.


# Установка и использование
Устанавливаем зависимости `pip install -r requirements.txt`
Для удобства хранения входных файлов вы можете располагать их в дирректории `General/input`. Если папки `input` не существует, создайте ее.

#### ВАЖНО: файлы принимаются только с расширениями (mp4, avi, mov)

После всех действий выше вы можете запускать файл `main.py`.
Результат выполнения вы сами сохраняете в нужное место на своем компьютере, программа предложит вам это сделать. Если вам интересно посмотреть как программа разбила видео на кадры, то можете открыть папку `General/results`.


# Уникальность проекта
### УЛУЧШЕНИЕ КАЧЕСТВА

Уникальность продукта обеспечивается использованием объектно-ориентированного программирования (ООП), которое позволяет структурировать код в виде взаимодействующих объектов, повышая его модульность, гибкость и упрощая разработку, тестирование и сопровождение.

Важным фактором является применение Генеративно-состязательной сети (GAN) в качестве алгоритма. GAN способна эффективно обучаться на больших объемах данных и улучшать результаты с каждой новой итерацией обучения, обеспечивая высокую точность и качество генерации изображений.

### ГЕНЕРАЦИЯ СУБТИТРОВ

Deepgram удивляет своей непревзойденной способностью преобразовывать речь в текст с высочайшей точностью. Независимо от условий записи, акцента и темпа речи, нейросеть обеспечивает невероятно точные результаты. Это открывает путь для эффективного чтения, обработки и анализа речевого контента.
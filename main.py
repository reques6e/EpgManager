import xml.etree.ElementTree as ET

from xml.dom import minidom
from datetime import datetime, timedelta

from exceptions import (
    TimeConvertError, ChannelNotFound, EpgError, ProgrammeNotFound, 
    TimeError, TimeFormatError, ChannelAlreadyExists
)

class EPG:
    def __init__(self):
        self.tv = ET.Element("tv")
        self.channels = {}

    def convert_to_epg_time(self, custom_time_str):

        """
        
        Конвектирует время

        Эта функция нужна только для удобства

        """

        try:
            date_part, time_part, tz_part = custom_time_str.split('.')
            date_time = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
            formatted_time = date_time.strftime("%Y%m%d%H%M00")  # Секунды всегда 00
            tz_hours = int(tz_part)
            tz_offset = f"{tz_hours:+03d}00"  # Форматируем смещение как ±HHMM
            return f"{formatted_time} {tz_offset}"
        except ValueError:
            raise TimeFormatError("Неверный формат времени. Используйте 'YYYY-MM-DD.HH:MM.+00'.")

    def add_channel(self, channel_id, display_name, icon_url=None):

        """
        
        Добавляет канал
        
        """

        if channel_id in self.channels:
            raise ChannelAlreadyExists(f"Канал {channel_id} уже существует.")
        
        channel = ET.SubElement(self.tv, "channel", id=channel_id)
        ET.SubElement(channel, "display-name").text = display_name
        if icon_url:
            ET.SubElement(channel, "icon", src=icon_url)
        self.channels[channel_id] = channel

    def add_programme(self, channel_id, start, stop, title, desc=None, category=None):

        """
        
        Добавляет программу для канала
        
        """

        if channel_id not in self.channels:
            raise ChannelNotFound(f"Канал {channel_id} не существует.")
        
        try:
            start_epg = self.convert_to_epg_time(start)
            stop_epg = self.convert_to_epg_time(stop)
        except ValueError as e:
            raise TimeConvertError(f"Ошибка при конвертации времени: {e}")
        
        if start_epg >= stop_epg:
            raise EpgError("Время начала должно быть раньше времени окончания.")
        
        for programme in self.tv.findall("programme"):
            if (programme.get("channel") == channel_id and 
                (start_epg < programme.get("stop") and stop_epg > programme.get("start"))):
                raise EpgError("Программа пересекается с уже существующей программой на данном канале.")
        
        programme = ET.SubElement(self.tv, "programme", start=start_epg, stop=stop_epg, channel=channel_id)
        ET.SubElement(programme, "title").text = title
        if desc:
            ET.SubElement(programme, "desc").text = desc
        if category:
            ET.SubElement(programme, "category").text = category
        else:
            ET.SubElement(programme, "category").text = "Uncategorized"

    def remove_channel(self, channel_id):

        """
        
        Удаляет канал
        
        """

        if channel_id not in self.channels:
            raise ChannelNotFound(f"Канал {channel_id} не существует.")
        
        for channel in self.tv.findall("channel"):
            if channel.get("id") == channel_id:
                self.tv.remove(channel)
                break

        for programme in self.tv.findall("programme"):
            if programme.get("channel") == channel_id:
                self.tv.remove(programme)
        
        if channel_id in self.channels:
            del self.channels[channel_id]

    def remove_programme(self, channel_id, start, stop):

        """
        
        Удаляет программу у канала
        
        """

        if channel_id not in self.channels:
            raise ChannelNotFound(f"Канал {channel_id} не существует.")
        
        try:
            start_epg = self.convert_to_epg_time(start)
            stop_epg = self.convert_to_epg_time(stop)
        except ValueError as e:
            raise TimeConvertError(f"Ошибка при конвертации времени: {e}")
        
        found = False
        for programme in self.tv.findall("programme"):
            if (programme.get("channel") == channel_id and 
                programme.get("start") == start_epg and 
                programme.get("stop") == stop_epg):
                self.tv.remove(programme)
                found = True
                break
        
        if not found:
            raise ProgrammeNotFound("Программа не найдена.")

    def prettify(self, elem):
        rough_string = ET.tostring(elem, encoding="utf-8")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def update_channel(self, channel_id, display_name=None, icon_url=None):

        """
        
        Обновляет уже существующий канал

        """

        if channel_id not in self.channels:
            raise ChannelNotFound(f"Канал {channel_id} не существует.")
        
        channel = self.channels[channel_id]
        
        if display_name:
            channel.find("display-name").text = display_name
        
        icon_element = channel.find("icon")
        if icon_url:
            if icon_element is None:
                ET.SubElement(channel, "icon", src=icon_url)
            else:
                icon_element.set("src", icon_url)
        elif icon_element is not None:
            channel.remove(icon_element)

    def update_programme(self, channel_id, old_start, old_stop, new_start=None, new_stop=None, title=None, desc=None, category=None):
        
        """
        
        Обновляет уже существующую программу у канала

        """

        if channel_id not in self.channels:
            raise ChannelNotFound(f"Канал {channel_id} не существует.")
        
        try:
            old_start_epg = self.convert_to_epg_time(old_start)
            old_stop_epg = self.convert_to_epg_time(old_stop)
        except ValueError as e:
            raise TimeConvertError(f"Ошибка при конвертации времени: {e}")
        
        programme = None
        for prog in self.tv.findall("programme"):
            if (prog.get("channel") == channel_id and 
                prog.get("start") == old_start_epg and 
                prog.get("stop") == old_stop_epg):
                programme = prog
                break
        
        if not programme:
            raise ProgrammeNotFound("Программа не найдена.")

        if new_start:
            new_start_epg = self.convert_to_epg_time(new_start)
            if new_start_epg >= programme.get("stop"):
                raise EpgError("Новое время начала должно быть раньше времени окончания.")
            programme.set("start", new_start_epg)
        
        if new_stop:
            new_stop_epg = self.convert_to_epg_time(new_stop)
            if programme.get("start") >= new_stop_epg:
                raise EpgError("Новое время окончания должно быть позже времени начала.")
            programme.set("stop", new_stop_epg)
        
        if title:
            programme.find("title").text = title
        
        if desc:
            desc_element = programme.find("desc")
            if desc_element is None:
                ET.SubElement(programme, "desc").text = desc
            else:
                desc_element.text = desc
        
        if category:
            category_element = programme.find("category")
            if category_element is None:
                ET.SubElement(programme, "category").text = category
            else:
                category_element.text = category
        else:
            category_element = programme.find("category")
            if category_element is None:
                ET.SubElement(programme, "category").text = "Без категории"
            else:
                category_element.text = "Без категории"
                
    def to_xml_string(self):

        """

        Конвектирует XML в текст

        """

        return self.prettify(self.tv)

    def save_to_file(self, file_name):

        """

        Сохраняет EPG в формате XML

        """

        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.to_xml_string())

class EPGCleaner:
    def __init__(self, epg, days=3):
        self.epg = epg
        self.days = days

    def remove_old_programmes(self):

        """

        Удаляет старую программу

        Для правильной работы требуется создать цикл с тайм аутом (1 день)

        """

        current_time = datetime.utcnow()
        threshold_time = current_time - timedelta(days=self.days)

        programmes_to_remove = []
        for programme in self.epg.tv.findall("programme"):
            start_time_str = programme.get("start").split(' ')[0]
            try:
                start_time = datetime.strptime(start_time_str, "%Y%m%d%H%M%S")
            except ValueError:
                raise EpgError("Ошибка при разборе времени программы.")
            
            if start_time < threshold_time:
                programmes_to_remove.append(programme)
        
        for programme in programmes_to_remove:
            self.epg.tv.remove(programme)


# Пример использования класса
epg = EPG()

# Добавляем каналы
epg.add_channel("1.tv_systema_1", "Система 1", "https://example.com/channel1.png")
epg.add_channel("2.tv_systema_2", "Система 2", "https://example.com/channel2.png")

# Добавляем программы
epg.add_programme("1.tv_systema_1", "2024-08-17.12:00.+00", "2024-08-17.13:00.+00", "Футбол", "Информация", "Спорт")
epg.add_programme("2.tv_systema_2", "2024-08-17.12:00.+00", "2024-08-17.13:00.+00", "Новости", "Информация", "Новости")

# Обновляем программу
epg.update_programme("1.tv_systema_1", "2024-08-17.12:00.+00", "2024-08-17.13:00.+00", title="тест", category="Новости")

# Удаляем канал и связанные с ним программы
#epg.remove_channel("1.tv_systema_1")

# Удаляем конкретную программу
#epg.remove_programme("2.tv_systema_2", "2024-08-17.12:00.+00", "2024-08-17.13:00.+00")

# Сохраняем XML в файл
epg.save_to_file("epg_pretty.xml")

# Вывод XML
print(epg.to_xml_string())

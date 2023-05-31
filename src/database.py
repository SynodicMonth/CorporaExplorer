# connect to a mysql database
import pymysql


class CorporaDatabase:
    def __init__(self):
        # connect to localhost
        self.conn = pymysql.connect(host='localhost',  # 数据库地址
                                    port=3306,  # 数据库端口
                                    user='root',  # 数据库用户名
                                    password='Jyxxsn124',  # 数据库密码
                                    db='corpora',  # 数据库名称
                                    charset='utf8mb4'  # 数据库编码
                                    )
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    def get_classes(self):
        self.cursor.execute('select * from classes')
        return self.cursor.fetchall()

    def add_class(self, class_name, teacher_name):
        try:
            self.cursor.execute('insert into classes (class_name, teacher_name) values (%s, %s)',
                                (class_name, teacher_name))
            self.conn.commit()
        except pymysql.err.OperationalError as e:
            raise RuntimeError('class name is null')

    def delete_class(self, class_id):
        try:
            self.cursor.execute('start transaction')
            self.cursor.execute('delete from filetag where files_file_id in '
                                '(select file_id from files where chapters_classes_class_id = %s)', class_id)
            self.cursor.execute('delete from textfiles where files_file_id in '
                                '(select file_id from files where chapters_classes_class_id = %s)', class_id)
            self.cursor.execute('delete from files where chapters_classes_class_id = %s', class_id)
            self.cursor.execute('delete from chapters where classes_class_id = %s', class_id)
            self.cursor.execute('delete from classes where class_id = %s', class_id)
            self.cursor.execute('commit')
        except Exception as e:
            self.cursor.execute('rollback')
            raise e

    def get_files(self, class_id):
        self.cursor.execute('select chapter_id, chapter_name, total_size from chapters where classes_class_id = %s',
                            class_id)
        chapters = self.cursor.fetchall()
        chapters = {chapter[0]: (chapter[1], chapter[2]) for chapter in chapters}
        files = {}
        for chapter in chapters.keys():
            self.cursor.execute('select file_id, file_name, file_address, file_type, file_size from files '
                                'where chapters_chapter_id = %s '
                                'and chapters_classes_class_id = %s', (chapter, class_id))
            files[chapter] = self.cursor.fetchall()
        return files, chapters

    def add_file(self, file_name, file_address, file_type, file_size, chapter_id, class_id) -> int:
        self.cursor.execute('insert into files (file_name, file_address, file_type, file_size, chapters_chapter_id,'
                            ' chapters_classes_class_id) values (%s, %s, %s, %s, %s, %s)',
                            (file_name, file_address, file_type, file_size, chapter_id, class_id))
        self.conn.commit()
        self.update_chapter_total_size(chapter_id, class_id)
        self.cursor.execute('select @@IDENTITY')
        return self.cursor.fetchone()[0]

    def delete_file(self, file_id):
        try:
            self.cursor.execute('start transaction')
            # get chapter_id and class_id
            self.cursor.execute('select chapters_chapter_id, chapters_classes_class_id from files where file_id = %s',
                                file_id)
            chapter_id, class_id = self.cursor.fetchone()
            # update chapter total size
            self.cursor.execute('delete from filetag where files_file_id = %s', file_id)
            self.cursor.execute('delete from textfiles where files_file_id = %s', file_id)
            self.cursor.execute('delete from files where file_id = %s', file_id)
            self.cursor.execute('call update_total_size(%s, %s)', (chapter_id, class_id))
            self.cursor.execute('commit')
        except Exception as e:
            self.cursor.execute('rollback')
            raise e

    def add_chapter(self, class_id, chapter_name):
        self.cursor.execute('insert into chapters (chapter_name, classes_class_id) values (%s, %s)',
                            (chapter_name, class_id))
        self.conn.commit()

    def delete_chapter(self, chapter_id):
        try:
            self.cursor.execute('start transaction')
            self.cursor.execute('delete from filetag where files_file_id in (select file_id from files where '
                                'chapters_chapter_id = %s)', chapter_id)
            self.cursor.execute('delete from textfiles where files_file_id in (select file_id from files where '
                                'chapters_chapter_id = %s)', chapter_id)
            self.cursor.execute('delete from files where chapters_chapter_id = %s', chapter_id)
            self.cursor.execute('delete from chapters where chapter_id = %s', chapter_id)
            self.cursor.execute('commit')
        except Exception as e:
            self.cursor.execute('rollback')
            raise e

    def update_chapter_total_size(self, chapter_id, classes_class_id):
        self.cursor.execute('call update_total_size(%s, %s)', (chapter_id, classes_class_id))
        self.conn.commit()

    def add_textfile(self, file_id, text):
        self.cursor.execute('insert into textfiles (files_file_id, content) values (%s, %s)', (file_id, text))
        self.conn.commit()

    def get_filetags(self, file_id):
        self.cursor.execute('select tag_id, tag_name from filetag, tagname where files_file_id = %s '
                            'and tag_id = tagname_tag_id', file_id)
        return self.cursor.fetchall()

    def delete_filetag(self, file_id, tag_id):
        self.cursor.execute('delete from filetag where files_file_id = %s and tagname_tag_id = %s', (file_id, tag_id))
        self.conn.commit()

    def add_filetag(self, file_id, tag_id):
        try:
            self.cursor.execute('insert into filetag (files_file_id, tagname_tag_id) values (%s, %s)',
                                (file_id, tag_id))
        except pymysql.err.IntegrityError as e:
            pass
        self.conn.commit()

    def add_tag(self, tag_name):
        self.cursor.execute('insert into tagname (tag_name) values (%s)', tag_name)
        self.conn.commit()

    def delete_tag(self, tag_id):
        self.cursor.execute('delete from filetag where tagname_tag_id = %s', tag_id)
        self.cursor.execute('delete from tagname where tag_id = %s', tag_id)
        self.conn.commit()

    def get_tags(self):
        self.cursor.execute('select tag_id, tag_name from tagname')
        return self.cursor.fetchall()

    def get_all_files(self):
        self.cursor.execute('select class_name, chapter_name, file_name from allfiles')
        return self.cursor.fetchall()

    def search(self, keyword):
        self.cursor.execute('select files_file_id, content from textfiles '
                            'where MATCH content AGAINST (%s IN NATURAL LANGUAGE MODE)', keyword)
        return self.cursor.fetchall()

    def get_file_info(self, file_id):
        self.cursor.execute('select file_name, file_address, file_type, file_size from files '
                            'where file_id = %s', file_id)
        return self.cursor.fetchone()

# data = CorporaDatabase()
# data.add_class('test', 'test')
# print(data.get_classes())
# data.add_file('test', 'test', 'test', 1, 2, data.get_classes()[0][0])
# print(data.get_files(data.get_classes()[0][0]))

# DB router for echomind app

class EchomindDBRouter(object):
    """
    A router to control echomind db operations
    """
    def db_for_read(self, model, **hints):
        "point all operations on echomind models to db 'echomind'"
        if model._meta.app_label == 'echomind':
            return 'echomind'
        return None

    def db_for_write(self, model, **hints):
        "point all operations on echomind models to db 'echomind'"
        if model._meta.app_label == 'echomind':
            return 'echomind'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "point all operations on echomind models to db 'echomind'"
        if obj1._meta.app_label == 'echomind' or \
           obj2._meta.app_label == 'echomind':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'echomind':
            return db == 'echomind'
        return None

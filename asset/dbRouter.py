# DB router for asset app

class AssetDBRouter(object):
    """
    A router to control asset db operations
    """
    def db_for_read(self, model, **hints):
        "point all operations on asset models to db 'asset'"
        if model._meta.app_label == 'asset':
            return 'asset'
        return None

    def db_for_write(self, model, **hints):
        "point all operations on asset models to db 'asset'"
        if model._meta.app_label == 'asset':
            return 'asset'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "point all operations on asset models to db 'asset'"
        if obj1._meta.app_label == 'asset' or \
           obj2._meta.app_label == 'asset':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'asset':
            return db == 'asset'
        return None

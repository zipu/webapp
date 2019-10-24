# DB router for trading app

class TradingDBRouter(object):
    """
    A router to control trading db operations
    """
    def db_for_read(self, model, **hints):
        "point all operations on trading models to db 'trading'"
        if model._meta.app_label == 'trading':
            return 'trading'
        return None

    def db_for_write(self, model, **hints):
        "point all operations on trading models to db 'trading'"
        if model._meta.app_label == 'trading':
            return 'trading'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "point all operations on trading models to db 'trading'"
        if obj1._meta.app_label == 'trading' or \
           obj2._meta.app_label == 'trading':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'trading':
            return db == 'trading'
        return None

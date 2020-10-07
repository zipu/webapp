# DB router for tutoring app

class TutoringDBRouter(object):
    """
    A router to control tutoring db operations
    """
    def db_for_read(self, model, **hints):
        "point all operations on tutoring models to db 'tutoring'"
        if model._meta.app_label == 'tutoring':
            return 'tutoring'
        return None

    def db_for_write(self, model, **hints):
        "point all operations on tutoring models to db 'tutoring'"
        if model._meta.app_label == 'tutoring':
            return 'tutoring'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "point all operations on tutoring models to db 'tutoring'"
        if obj1._meta.app_label == 'tutoring' or \
           obj2._meta.app_label == 'tutoring':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'tutoring':
            return db == 'tutoring'
        return None

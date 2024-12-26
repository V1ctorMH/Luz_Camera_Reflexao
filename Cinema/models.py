from app import db

class Usuario(db.Model):
    __tablename__ = 'usuario'

    Id = db.Column(db.Integer, primary_key=True)
    Email = db.Column(db.String(150), unique=True, nullable=False)
    Nome = db.Column(db.String(150), nullable=False)
    Senha = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

    __table_args__ = {'extend_existing': True}

    def get_id(self):
        return str(self.Id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
import hashlib
import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    mapped_column,
    relationship,
    sessionmaker,
)

DB_URL = 'sqlite:///database.db'
engine = sa.create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

session = Session()

class FriendsAssociation(Base):
    """Class avoiding circular dependencies between users."""
    __tablename__ = 'friends_association'

    id = mapped_column(sa.Integer, primary_key=True)
    user_id = mapped_column(sa.Integer, sa.ForeignKey('users.id'))
    friend_id = mapped_column(sa.Integer, sa.ForeignKey('users.id'))


class User(Base):
    """User class."""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    auth: Mapped['UserAuth'] = relationship(
        # there's a one-to-one relationship between this class and UserAuth class
        # one user has exactly one UserAuth
        'UserAuth', uselist=False, back_populates='user' # back_populates syncs the relatioships between the different tables
    )
    points: Mapped[int]
    
    # list of friends who are also users
    friends = relationship(
        # there's a one-to-many relationship between this class and User class itself
        # one user has a list of many friends(Users)
        'User', secondary='friends_association', 
        primaryjoin=('FriendsAssociation.user_id==User.id'),
        secondaryjoin=('FriendsAssociation.friend_id==User.id')
    )

    challenges_list: Mapped[list['FriendChallenge']] = relationship(
        'FriendChallenge', back_populates='user')

    def __init__(self, username, password):
        self.points = 1
        self.auth = UserAuth(username, password)

    def __repr__(self):
        return f'<User(username={self.auth.username}, friends={self.friends})>'


class UserAuth(Base):
    """User authentication class."""
    __tablename__ = 'user_auth'

    id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey('users.id'), primary_key=True, index=True, unique=True)
    username: Mapped[str] = mapped_column(index=True, unique=True)
    password_hash: Mapped[str]
    user: Mapped['User'] = relationship(back_populates='auth')

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def __repr__(self):
        return f'<UserAuth(username={self.username})>'


class FriendChallenge(Base):
    """Challenge sent by friend."""
    __tablename__ = 'challenges'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey('users.id'))
    user: Mapped['User'] = relationship(back_populates='challenges_list')
    sender_id: Mapped[int]
    word: Mapped[str]
    hint: Mapped[str]
    is_used: Mapped[bool]

    def __init__(self, sender_id, word, hint, is_used=False):
        self.sender_id = sender_id
        self.word = word
        self.hint = hint
        self.is_used = is_used

    def __repr__(self):
        return f'<Challenge(word={self.word}, hint={self.hint})>'


Base.metadata.create_all(engine)
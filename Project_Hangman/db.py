import bcrypt
import os
import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    mapped_column,
    relationship,
    sessionmaker,
    scoped_session,
)
from sqlalchemy.pool import StaticPool
from constants import BASE_DIR

DB_PATH = BASE_DIR / 'database.db'
DB_URL = os.environ.get('HANGMAN_DB_URL', f'sqlite:///{DB_PATH.as_posix()}')

engine_kwargs = {}
if DB_URL.startswith('sqlite'):
    engine_kwargs['connect_args'] = {'check_same_thread': False}
if DB_URL in ('sqlite://', 'sqlite:///:memory:'):
    engine_kwargs['poolclass'] = StaticPool # one shared database for all threads

engine = sa.create_engine(DB_URL, **engine_kwargs)
Session = sessionmaker(bind=engine)
Base = declarative_base()

session = scoped_session(Session) # thread-safe sessions for multiple client sockets

class FriendsAssociation(Base):
    """Class avoiding circular dependencies between users."""
    __tablename__ = 'friends_association'
    __table_args__ = (
        sa.UniqueConstraint('user_id', 'friend_id'),
        sa.CheckConstraint('user_id != friend_id'),   # can't befriend yourself
    )

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
        'FriendChallenge', back_populates='user', 
        foreign_keys='FriendChallenge.user_id')

    def __init__(self, username, password):
        self.points = 1
        self.auth = UserAuth(username, password)

    def add_friend(self, friend):
        """Create a two-way friendship."""
        if friend is self or friend in self.friends:
            return False
        self.friends.append(friend)
        if self not in friend.friends:
            friend.friends.append(self)
        return True

    def __repr__(self):
        return f'<User(username={self.auth.username}, friends={[f.auth.username for f in self.friends]})>'


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
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())
    
    def __repr__(self):
        return f'<UserAuth(username={self.username})>'


class FriendChallenge(Base):
    """Challenge sent by friend."""
    __tablename__ = 'challenges'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(sa.ForeignKey('users.id'))
    sender_id: Mapped[int] = mapped_column(sa.ForeignKey('users.id'))
    user: Mapped['User'] = relationship(back_populates='challenges_list', foreign_keys=[user_id])
    sender: Mapped['User'] = relationship(foreign_keys=[sender_id])
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
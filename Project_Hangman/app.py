from db import session, User, FriendChallenge

def seed():
    """Seed the database with initial data."""
    if session.query(User).count() > 0:
        print('Database is seeded already.')
        return
    user1 = User("mariana.terzieva", "lolo")
    user2 = User("christina.aguilera", "lala")
    user3 = User("tom_cruise", "maverick")
    user4 = User("lionel.messi", "barcelona")

    session.add_all([user1, user2, user3, user4])
    session.flush() # flush assigns IDs without committing

    user1.add_friend(user2)
    user1.add_friend(user3)
    user1.challenges_list.append(
        FriendChallenge(user2.id, 'бостан', 'диня; нива за дини'))

    session.commit()

    for user in (user1, user2, user3, user4):
        print(f"{user.auth.username} has {len(user.friends)} friends and {len(user.challenges_list)} challenges.")


if __name__ == '__main__':
    seed()
    session.remove()
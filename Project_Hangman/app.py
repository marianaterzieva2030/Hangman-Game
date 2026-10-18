from db import session, User, FriendChallenge

user1 = User("mariana.terzieva", "lolo")
user2 = User("velina.terzieva", "op")
user3 = User("tedie.terzieva", "sql")
user4 = User("angel.terziev", "milan")

user1.friends.append(user2)
user1.friends.append(user3)
user2.friends.append(user1) # circular dependency error fixed

user1.challenges_list.append(FriendChallenge(2, 'бостан', 'диня; нива за дини'))

session.add_all([user1, user2, user3, user4])
session.commit()

print(f"{user1.friends = }")
print(f"{user2.friends = }")
print(f"{user3.friends = }")
print(f"{user4.friends = }")
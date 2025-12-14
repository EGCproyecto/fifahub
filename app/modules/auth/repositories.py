from app.modules.auth.models import User, UserFollowAuthor, UserFollowCommunity
from core.repositories.BaseRepository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    def create(self, commit: bool = True, **kwargs):
        password = kwargs.pop("password")
        instance = self.model(**kwargs)
        instance.set_password(password)
        self.session.add(instance)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return instance

    def get_by_email(self, email: str):
        return self.model.query.filter_by(email=email).first()


class UserFollowAuthorRepository(BaseRepository):
    def __init__(self):
        super().__init__(UserFollowAuthor)

    def get_by_user_and_author(self, user_id: int, author_id: int):
        return self.model.query.filter_by(user_id=user_id, author_id=author_id).first()

    def get_for_user(self, user_id: int):
        return self.model.query.filter_by(user_id=user_id).all()

    def get_for_author(self, author_id: int):
        return self.model.query.filter_by(author_id=author_id).all()

    def delete_by_user_and_author(self, user_id: int, author_id: int) -> bool:
        instance = self.get_by_user_and_author(user_id, author_id)
        if not instance:
            return False
        self.session.delete(instance)
        self.session.commit()
        return True


class UserFollowCommunityRepository(BaseRepository):
    def __init__(self):
        super().__init__(UserFollowCommunity)

    def get_by_user_and_community(self, user_id: int, community_id: str):
        return self.model.query.filter_by(user_id=user_id, community_id=community_id).first()

    def get_for_user(self, user_id: int):
        return self.model.query.filter_by(user_id=user_id).all()

    def get_for_community(self, community_id: str):
        return self.model.query.filter_by(community_id=community_id).all()

    def delete_by_user_and_community(self, user_id: int, community_id: str) -> bool:
        instance = self.get_by_user_and_community(user_id, community_id)
        if not instance:
            return False
        self.session.delete(instance)
        self.session.commit()
        return True

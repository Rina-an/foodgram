from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (AvatarView,
                       DownloadShoppingCartView,
                       FavoriteView,
                       IngredientViewSet,
                       RecipeShortLinkView,
                       RecipeViewSet,
                       ShoppingCartView,
                       SubscribeView,
                       SubscriptionListView,
                       TagViewSet,
                       UserViewSet,
                       )

router = DefaultRouter()

router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('users/me/avatar/',
         AvatarView.as_view(),
         name='avatar'
         ),
    path('users/subscriptions/',
         SubscriptionListView.as_view(),
         name='subscriptions'
         ),
    path('users/<int:user_id>/subscribe/',
         SubscribeView.as_view(),
         name='subscribe'
         ),
    path('recipes/download_shopping_cart/',
         DownloadShoppingCartView.as_view(),
         name='download_shopping_cart'
         ),
    path('recipes/<int:recipe_id>/favorite/',
         FavoriteView.as_view(),
         name='favorite'
         ),
    path('recipes/<int:recipe_id>/shopping_cart/',
         ShoppingCartView.as_view(),
         name='shopping_cart'
         ),
    path('recipes/<int:recipe_id>/get-link/',
         RecipeShortLinkView.as_view(),
         name='get_link'
         ),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

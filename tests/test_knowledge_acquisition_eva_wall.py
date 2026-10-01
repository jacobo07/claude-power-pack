"""classify_wall: an auth wall needs structural evidence, not a word.

Origin 2026-10-01: EVA Unified ends every conversation with "No compartas
contraseñas ni datos sensibles". eva-adapter/1.0.0 scanned the whole frame for
'contraseña' and paused the run as NEEDS_HUMAN five seconds into the first
pilot prompt, while EVA was answering normally (4,589 chars captured in history).
"""
from modules.knowledge_acquisition.eva_adapter import classify_wall

EVA_FOOTER = ("EVA utiliza IA y puede equivocarse. No compartas contraseñas "
              "ni datos sensibles.")
LOGIN_PAGE = "Iniciar sesión\nCorreo electrónico\nContraseña\n¿Olvidaste tu contraseña?"


def test_eva_disclaimer_with_composer_is_not_a_wall():
    # Arrange: the real chrome of a logged-in conversation
    chrome = "EVA\nNuevo Chat\nProyectos\nPerfil\n" + EVA_FOOTER
    # Act
    hit = classify_wall(chrome, has_password_field=False, has_composer=True)
    # Assert
    assert hit is None


def test_login_page_with_password_field_is_a_wall():
    # Positive control: the same word is a wall when the page is a login form
    hit = classify_wall(LOGIN_PAGE, has_password_field=True, has_composer=False)
    assert hit is not None


def test_credential_word_without_composer_is_a_wall():
    # Logged out to a page with no chat box and no password field rendered yet
    hit = classify_wall("Iniciar sesión", has_password_field=False, has_composer=False)
    assert hit == "iniciar sesión"


def test_password_field_beside_composer_is_still_a_wall():
    # A re-auth modal over the chat: composer present, but a password is demanded
    hit = classify_wall("Vuelve a introducir tu contraseña", has_password_field=True,
                        has_composer=True)
    assert hit == "contraseña"


def test_rate_limit_in_chrome_is_a_wall_even_with_composer():
    # Throttle markers are not credential words: they fire on the chrome alone
    hit = classify_wall("Too many requests. Try again later.",
                        has_password_field=False, has_composer=True)
    assert hit == "too many requests"


def test_clean_chrome_is_not_a_wall():
    hit = classify_wall("EVA\nNuevo Chat\nBuenas tardes, Jacobo",
                        has_password_field=False, has_composer=True)
    assert hit is None

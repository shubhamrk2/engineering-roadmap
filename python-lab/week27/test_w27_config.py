"""Marker for w27_config.py. Run from python-lab/:  python -m pytest week27 -q"""
import pytest

from w27_config import (ConfigError, Settings, build_run_command, get_env, load_settings,
                        redact_url, to_bool, to_int, validate_compose)

GOOD_ENV = {"DATABASE_URL": "postgresql://app:s3cret@db:5432/app", "API_KEY": "k-12345"}


# ---------- get_env ----------
def test_get_env_returns_stripped_value():
    assert get_env({"A": "  hi "}, "A") == "hi"


def test_get_env_missing_uses_default():
    assert get_env({}, "A", default="x") == "x"
    assert get_env({}, "A") is None


def test_get_env_empty_and_blank_count_as_unset():
    assert get_env({"A": ""}, "A", default="d") == "d"
    assert get_env({"A": "   "}, "A", default="d") == "d"


def test_get_env_required_missing_names_the_setting():
    with pytest.raises(ConfigError, match="DATABASE_URL"):
        get_env({}, "DATABASE_URL", required=True)


def test_get_env_required_blank_also_raises():
    with pytest.raises(ConfigError, match="A"):
        get_env({"A": " "}, "A", required=True)


def test_get_env_required_present_does_not_raise():
    assert get_env({"A": "1"}, "A", default="z", required=True) == "1"


# ---------- to_bool ----------
@pytest.mark.parametrize("text", ["true", "TRUE", "1", "yes", "On", " true "])
def test_to_bool_truthy(text):
    assert to_bool(text) is True


@pytest.mark.parametrize("text", ["false", "False", "0", "no", "OFF", " 0 "])
def test_to_bool_falsy(text):
    assert to_bool(text) is False


def test_to_bool_rejects_other_text_and_names_setting():
    with pytest.raises(ConfigError, match="DEBUG"):
        to_bool("maybe", "DEBUG")
    with pytest.raises(ConfigError):
        to_bool("")


# ---------- to_int ----------
def test_to_int_parses_with_spaces():
    assert to_int(" 8080 ") == 8080
    assert to_int("-3") == -3


def test_to_int_not_a_number():
    with pytest.raises(ConfigError, match="PORT"):
        to_int("80a", "PORT")
    with pytest.raises(ConfigError):
        to_int("1.5")


def test_to_int_bounds_inclusive():
    assert to_int("1", "P", minimum=1, maximum=65535) == 1
    assert to_int("65535", "P", minimum=1, maximum=65535) == 65535
    with pytest.raises(ConfigError, match="P"):
        to_int("0", "P", minimum=1)
    with pytest.raises(ConfigError, match="P"):
        to_int("65536", "P", maximum=65535)


# ---------- redact_url ----------
def test_redact_url_hides_password_only():
    assert redact_url("postgresql://app:s3cret@db:5432/app") == "postgresql://app:***@db:5432/app"


def test_redact_url_without_password_unchanged():
    assert redact_url("postgresql://db:5432/app") == "postgresql://db:5432/app"
    assert redact_url("postgresql://app@db/app") == "postgresql://app@db/app"
    assert redact_url("not a url") == "not a url"


def test_redact_url_other_schemes():
    assert redact_url("redis://u:p@cache:6379/0") == "redis://u:***@cache:6379/0"


# ---------- load_settings / Settings ----------
def test_load_settings_defaults():
    s = load_settings(GOOD_ENV)
    assert s == Settings("postgresql://app:s3cret@db:5432/app", "k-12345", 8000, False, "INFO")


def test_load_settings_full_override_and_coercion():
    env = dict(GOOD_ENV, PORT="9000", DEBUG="yes", LOG_LEVEL="warning")
    s = load_settings(env)
    assert (s.port, s.debug, s.log_level) == (9000, True, "WARNING")
    assert isinstance(s.port, int)


@pytest.mark.parametrize("missing", ["DATABASE_URL", "API_KEY"])
def test_load_settings_required(missing):
    env = {k: v for k, v in GOOD_ENV.items() if k != missing}
    with pytest.raises(ConfigError, match=missing):
        load_settings(env)


def test_load_settings_port_range_edges_are_valid():
    assert load_settings(dict(GOOD_ENV, PORT="1")).port == 1
    assert load_settings(dict(GOOD_ENV, PORT="65535")).port == 65535


@pytest.mark.parametrize("bad", [{"PORT": "0"}, {"PORT": "70000"}, {"PORT": "abc"}])
def test_load_settings_bad_port(bad):
    with pytest.raises(ConfigError, match="PORT"):
        load_settings(dict(GOOD_ENV, **bad))


def test_load_settings_bad_debug_and_level():
    with pytest.raises(ConfigError, match="DEBUG"):
        load_settings(dict(GOOD_ENV, DEBUG="sure"))
    with pytest.raises(ConfigError, match="LOG_LEVEL"):
        load_settings(dict(GOOD_ENV, LOG_LEVEL="chatty"))


def test_load_settings_blank_optional_uses_default():
    s = load_settings(dict(GOOD_ENV, PORT="", DEBUG=" ", LOG_LEVEL=""))
    assert (s.port, s.debug, s.log_level) == (8000, False, "INFO")


def test_settings_repr_and_str_never_leak_secrets():
    s = load_settings(GOOD_ENV)
    for text in (repr(s), str(s), f"{s}", f"{s!r}"):
        assert "s3cret" not in text
        assert "k-12345" not in text
        assert "api_key='***'" in text
        assert "app:***@db" in text


def test_settings_repr_shows_other_fields():
    text = repr(load_settings(dict(GOOD_ENV, PORT="9001", DEBUG="1")))
    assert text.startswith("Settings(")
    assert "port=9001" in text and "debug=True" in text and "log_level='INFO'" in text


# ---------- validate_compose ----------
def good_doc():
    return {
        "services": {
            "api": {
                "build": ".",
                "ports": ["8000:8000"],
                "environment": {"DATABASE_URL": "${DATABASE_URL}", "API_KEY": "${API_KEY}"},
                "depends_on": {"db": {"condition": "service_healthy"}},
            },
            "db": {
                "image": "postgres:16",
                "environment": ["POSTGRES_PASSWORD=${DB_PASSWORD}"],
                "volumes": ["pgdata:/var/lib/postgresql/data", "./init:/docker-entrypoint-initdb.d"],
                "healthcheck": {"test": ["CMD-SHELL", "pg_isready -U app"]},
            },
        },
        "volumes": {"pgdata": {}},
    }


def test_compose_good_doc_has_no_problems():
    assert validate_compose(good_doc()) == []


@pytest.mark.parametrize("doc", [{}, {"services": {}}, {"services": None}, {"version": "3"}])
def test_compose_no_services(doc):
    assert validate_compose(doc) == ["no services defined"]


def test_compose_needs_image_or_build():
    d = good_doc()
    d["services"]["api"] = {"ports": ["8000:8000"]}
    assert validate_compose(d) == ["api: needs image or build"]


@pytest.mark.parametrize("image", ["postgres", "postgres:latest", "ghcr.io/acme/web", "localhost:5000/web"])
def test_compose_unpinned_image(image):
    d = good_doc()
    d["services"]["db"]["image"] = image
    assert validate_compose(d) == ["db: image is not pinned"]


@pytest.mark.parametrize("image", ["postgres:16", "pgvector/pgvector:pg16", "localhost:5000/web:1.2", "postgres@sha256:abc123"])
def test_compose_pinned_image_ok(image):
    d = good_doc()
    d["services"]["db"]["image"] = image
    assert validate_compose(d) == []


@pytest.mark.parametrize("entry", ["8000", "8000:", "0:80", "80:70000", "a:b", 8000, "80:80:80"])
def test_compose_bad_ports(entry):
    d = good_doc()
    d["services"]["api"]["ports"] = [entry]
    assert validate_compose(d) == [f"api: bad port {entry}"]


def test_compose_hard_coded_secret_dict_and_list():
    d = good_doc()
    d["services"]["api"]["environment"]["API_KEY"] = "abc123"
    d["services"]["db"]["environment"] = ["POSTGRES_PASSWORD=hunter2"]
    problems = validate_compose(d)
    assert "api: secret API_KEY is hard-coded" in problems
    assert "db: secret POSTGRES_PASSWORD is hard-coded" in problems
    assert len(problems) == 2


def test_compose_secret_key_match_is_case_insensitive_and_substring():
    d = good_doc()
    d["services"]["api"]["environment"] = {"my_token": "x", "LOG_LEVEL": "info", "APIKEY_X": "y"}
    assert sorted(validate_compose(d)) == ["api: secret APIKEY_X is hard-coded", "api: secret my_token is hard-coded"]


def test_compose_empty_secret_value_is_not_flagged():
    d = good_doc()
    d["services"]["api"]["environment"] = {"API_KEY": None, "DB_PASSWORD": ""}
    assert validate_compose(d) == []


def test_compose_depends_on_unknown_service_list_form():
    d = good_doc()
    d["services"]["api"]["depends_on"] = ["cache"]
    assert validate_compose(d) == ["api: depends_on unknown service cache"]


def test_compose_service_healthy_needs_healthcheck():
    d = good_doc()
    del d["services"]["db"]["healthcheck"]
    assert validate_compose(d) == ["api: db has no healthcheck"]


def test_compose_service_started_does_not_need_healthcheck():
    d = good_doc()
    del d["services"]["db"]["healthcheck"]
    d["services"]["api"]["depends_on"] = {"db": {"condition": "service_started"}}
    assert validate_compose(d) == []
    d["services"]["api"]["depends_on"] = ["db"]
    assert validate_compose(d) == []


def test_compose_undeclared_named_volume():
    d = good_doc()
    d["volumes"] = {}
    assert validate_compose(d) == ["volume pgdata is not declared"]
    del d["volumes"]
    assert validate_compose(d) == ["volume pgdata is not declared"]


def test_compose_bind_mounts_are_not_named_volumes():
    d = good_doc()
    d["services"]["api"]["volumes"] = ["./src:/app/src", "/var/log:/logs", "~/data:/data", "/anonymous"]
    assert validate_compose(d) == []


def test_compose_reports_every_problem():
    d = {"services": {"web": {"ports": ["x"], "depends_on": ["ghost"], "environment": {"SECRET": "s"}}}}
    assert sorted(validate_compose(d)) == sorted([
        "web: needs image or build",
        "web: bad port x",
        "web: secret SECRET is hard-coded",
        "web: depends_on unknown service ghost",
    ])


def test_compose_null_service_body_does_not_crash():
    assert validate_compose({"services": {"x": None}}) == ["x: needs image or build"]


# ---------- build_run_command ----------
def test_run_minimal():
    assert build_run_command("api:1") == ["docker", "run", "-d", "api:1"]


def test_run_no_detach_and_remove():
    assert build_run_command("api:1", detach=False, remove=True) == ["docker", "run", "--rm", "api:1"]


def test_run_full_order():
    cmd = build_run_command(
        "api:1", name="api", ports={9000: 8000, 8080: 80}, env={"B": "2", "A": "1"},
        env_file=".env", volumes=["data:/data", "./src:/app/src"], remove=True)
    assert cmd == ["docker", "run", "-d", "--rm", "--name", "api",
                   "-p", "8080:80", "-p", "9000:8000",
                   "-e", "A=1", "-e", "B=2", "--env-file", ".env",
                   "-v", "data:/data", "-v", "./src:/app/src", "api:1"]


def test_run_env_none_passes_name_only():
    cmd = build_run_command("api:1", env={"API_KEY": None, "MODE": "dev"})
    assert cmd == ["docker", "run", "-d", "-e", "API_KEY", "-e", "MODE=dev", "api:1"]
    assert "API_KEY=None" not in cmd


def test_run_returns_list_of_str_and_image_is_last():
    cmd = build_run_command("api:1", ports={8000: 8000})
    assert isinstance(cmd, list) and all(isinstance(x, str) for x in cmd)
    assert cmd[-1] == "api:1"


@pytest.mark.parametrize("ports", [{0: 80}, {80: 70000}, {"80": 80}, {80: "80"}, {True: 80}])
def test_run_bad_ports(ports):
    with pytest.raises(ValueError):
        build_run_command("api:1", ports=ports)


@pytest.mark.parametrize("image", ["", None])
def test_run_requires_image(image):
    with pytest.raises(ValueError):
        build_run_command(image)


def test_run_does_not_mutate_arguments():
    ports, env, vols = {9000: 8000}, {"A": "1"}, ["v:/v"]
    build_run_command("x:1", ports=ports, env=env, volumes=vols)
    assert ports == {9000: 8000} and env == {"A": "1"} and vols == ["v:/v"]

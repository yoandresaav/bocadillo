from bocadillo import API


def test_index_returns_404_by_default(api: API):
    assert api.client.get("/").status_code == 404


def test_if_route_not_registered_then_404(api: API):
    assert api.client.get("/test").status_code == 404


def test_if_route_registered_then_not_404(api: API):
    @api.route("/")
    async def index(req, res):
        pass

    assert api.client.get("/").status_code != 404


def test_default_status_code_is_200_on_routes(api: API):
    @api.route("/")
    async def index(req, res):
        pass

    assert api.client.get("/").status_code == 200


def test_leading_slash_is_added_if_not_present(api: API):
    @api.route("foo")
    async def index(req, res):
        pass

    assert api.client.get("/foo").status_code == 200

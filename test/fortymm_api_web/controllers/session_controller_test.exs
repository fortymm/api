defmodule FortymmApiWeb.SessionControllerTest do
  use FortymmApiWeb.ConnCase

  test "GET /api/v1/session returns username and sets auth cookie", %{conn: conn} do
    conn = get(conn, ~p"/api/v1/session")

    assert json_response(conn, 200) == %{"username" => "Guest"}
    assert %{"auth" => %{value: token}} = conn.resp_cookies
    assert is_binary(token) and byte_size(token) > 0
  end

  test "auth cookie is http_only", %{conn: conn} do
    conn = get(conn, ~p"/api/v1/session")

    assert %{"auth" => cookie_opts} = conn.resp_cookies
    assert cookie_opts[:http_only] == true
  end

  test "auth token is a valid Phoenix token", %{conn: conn} do
    conn = get(conn, ~p"/api/v1/session")

    %{"auth" => %{value: token}} = conn.resp_cookies
    assert {:ok, "guest"} = Phoenix.Token.verify(FortymmApiWeb.Endpoint, "auth", token)
  end
end

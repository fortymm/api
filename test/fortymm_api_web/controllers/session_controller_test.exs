defmodule FortymmApiWeb.SessionControllerTest do
  use FortymmApiWeb.ConnCase

  describe "GET /api/v1/session without existing token" do
    test "returns username and sets auth cookie", %{conn: conn} do
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

  describe "GET /api/v1/session with existing valid token" do
    test "returns username without setting a new cookie", %{conn: conn} do
      existing_token = Phoenix.Token.sign(FortymmApiWeb.Endpoint, "auth", "guest")

      conn =
        conn
        |> put_req_cookie("auth", existing_token)
        |> get(~p"/api/v1/session")

      assert json_response(conn, 200) == %{"username" => "Guest"}
      assert conn.resp_cookies == %{}
    end
  end

  describe "GET /api/v1/session with invalid token" do
    test "creates a new session with fresh token", %{conn: conn} do
      conn =
        conn
        |> put_req_cookie("auth", "invalid_token")
        |> get(~p"/api/v1/session")

      assert json_response(conn, 200) == %{"username" => "Guest"}
      assert %{"auth" => %{value: token}} = conn.resp_cookies
      assert {:ok, "guest"} = Phoenix.Token.verify(FortymmApiWeb.Endpoint, "auth", token)
    end
  end
end

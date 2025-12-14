defmodule FortymmApiWeb.AccountControllerTest do
  use FortymmApiWeb.ConnCase

  alias FortymmApi.Accounts

  @session_cookie_name "fortymm_session"

  describe "PATCH /api/v1/account" do
    test "updates username when authenticated", %{conn: conn} do
      {:ok, user} = Accounts.create_anonymous_user()
      token = Accounts.generate_user_session_token(user)

      conn =
        conn
        |> put_req_cookie(@session_cookie_name, token)
        |> patch(~p"/api/v1/account", %{username: "newusername"})

      response = json_response(conn, 200)
      assert response["username"] == "newusername"
      assert response["email"] == nil
      assert response["has_password"] == false
    end

    test "returns updated user data including email and password status", %{conn: conn} do
      user = FortymmApi.AccountsFixtures.user_fixture()
      user = FortymmApi.AccountsFixtures.set_password(user)
      token = Accounts.generate_user_session_token(user)

      conn =
        conn
        |> put_req_cookie(@session_cookie_name, token)
        |> patch(~p"/api/v1/account", %{username: "updatedname"})

      response = json_response(conn, 200)
      assert response["username"] == "updatedname"
      assert response["email"] == user.email
      assert response["has_password"] == true
    end

    test "returns error when username is too short", %{conn: conn} do
      {:ok, user} = Accounts.create_anonymous_user()
      token = Accounts.generate_user_session_token(user)

      conn =
        conn
        |> put_req_cookie(@session_cookie_name, token)
        |> patch(~p"/api/v1/account", %{username: "ab"})

      response = json_response(conn, 422)
      assert response["errors"]["username"] != nil
    end

    test "returns error when username is too long", %{conn: conn} do
      {:ok, user} = Accounts.create_anonymous_user()
      token = Accounts.generate_user_session_token(user)

      conn =
        conn
        |> put_req_cookie(@session_cookie_name, token)
        |> patch(~p"/api/v1/account", %{username: String.duplicate("a", 21)})

      response = json_response(conn, 422)
      assert response["errors"]["username"] != nil
    end

    test "returns error when username has invalid characters", %{conn: conn} do
      {:ok, user} = Accounts.create_anonymous_user()
      token = Accounts.generate_user_session_token(user)

      conn =
        conn
        |> put_req_cookie(@session_cookie_name, token)
        |> patch(~p"/api/v1/account", %{username: "invalid@name"})

      response = json_response(conn, 422)
      assert response["errors"]["username"] != nil
    end

    test "returns error when username is already taken", %{conn: conn} do
      {:ok, existing_user} = Accounts.create_anonymous_user()
      {:ok, _} = Accounts.update_username(existing_user, %{username: "takenname"})

      {:ok, user} = Accounts.create_anonymous_user()
      token = Accounts.generate_user_session_token(user)

      conn =
        conn
        |> put_req_cookie(@session_cookie_name, token)
        |> patch(~p"/api/v1/account", %{username: "takenname"})

      response = json_response(conn, 422)
      assert response["errors"]["username"] != nil
    end

    test "username uniqueness is case-insensitive", %{conn: conn} do
      {:ok, existing_user} = Accounts.create_anonymous_user()
      {:ok, _} = Accounts.update_username(existing_user, %{username: "TakenName"})

      {:ok, user} = Accounts.create_anonymous_user()
      token = Accounts.generate_user_session_token(user)

      conn =
        conn
        |> put_req_cookie(@session_cookie_name, token)
        |> patch(~p"/api/v1/account", %{username: "takenname"})

      response = json_response(conn, 422)
      assert response["errors"]["username"] != nil
    end

    test "returns 401 when not authenticated", %{conn: conn} do
      conn = patch(conn, ~p"/api/v1/account", %{username: "newusername"})

      response = json_response(conn, 401)
      assert response["error"] == "Not authenticated"
    end

    test "returns 401 when token is invalid", %{conn: conn} do
      conn =
        conn
        |> put_req_cookie(@session_cookie_name, "invalid_token")
        |> patch(~p"/api/v1/account", %{username: "newusername"})

      response = json_response(conn, 401)
      assert response["error"] == "Not authenticated"
    end

    test "returns 400 when username parameter is missing", %{conn: conn} do
      {:ok, user} = Accounts.create_anonymous_user()
      token = Accounts.generate_user_session_token(user)

      conn =
        conn
        |> put_req_cookie(@session_cookie_name, token)
        |> patch(~p"/api/v1/account", %{})

      response = json_response(conn, 400)
      assert response["error"] == "Missing required parameter: username"
    end
  end
end

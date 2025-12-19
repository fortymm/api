defmodule FortymmApiWeb.RegistrationControllerTest do
  use FortymmApiWeb.ConnCase, async: true

  import FortymmApi.AccountsFixtures
  alias FortymmApi.Accounts

  describe "POST /api/v1/users" do
    test "registers a new user and sends confirmation email", %{conn: conn} do
      email = unique_user_email()

      conn =
        post(conn, ~p"/api/v1/users", %{
          "user" => %{"email" => email}
        })

      assert json_response(conn, 201) == %{
               "message" => "Registration successful. Please check your email to confirm your account."
             }

      # Verify user was created
      user = Accounts.get_user_by_email(email)
      assert user
      refute user.confirmed_at
      assert user.username
    end

    test "returns validation error for invalid email format", %{conn: conn} do
      conn =
        post(conn, ~p"/api/v1/users", %{
          "user" => %{"email" => "invalid-email"}
        })

      assert %{"errors" => %{"email" => [error]}} = json_response(conn, 422)
      assert error =~ "must have the @ sign"
    end

    test "returns validation error for missing email", %{conn: conn} do
      conn =
        post(conn, ~p"/api/v1/users", %{
          "user" => %{}
        })

      assert %{"errors" => %{"email" => ["can't be blank"]}} = json_response(conn, 422)
    end

    test "returns validation error for duplicate email", %{conn: conn} do
      existing_user = user_fixture()

      conn =
        post(conn, ~p"/api/v1/users", %{
          "user" => %{"email" => existing_user.email}
        })

      assert %{"errors" => %{"email" => ["has already been taken"]}} = json_response(conn, 422)
    end

    test "returns error when user params are missing", %{conn: conn} do
      conn = post(conn, ~p"/api/v1/users", %{})

      assert %{"errors" => %{"user" => ["is required"]}} = json_response(conn, 422)
    end

    test "returns validation error for email that is too long", %{conn: conn} do
      long_email = String.duplicate("a", 160) <> "@example.com"

      conn =
        post(conn, ~p"/api/v1/users", %{
          "user" => %{"email" => long_email}
        })

      assert %{"errors" => %{"email" => [error]}} = json_response(conn, 422)
      assert error =~ "should be at most"
    end
  end
end

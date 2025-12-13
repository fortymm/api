defmodule FortymmApiWeb.SessionController do
  use FortymmApiWeb, :controller

  def index(conn, _params) do
    token = Phoenix.Token.sign(FortymmApiWeb.Endpoint, "auth", "guest")

    conn
    |> put_resp_cookie("auth", token, http_only: true)
    |> json(%{username: "Guest"})
  end
end

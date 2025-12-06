defmodule FortymmApiWeb.PageController do
  use FortymmApiWeb, :controller

  def home(conn, _params) do
    render(conn, :home)
  end
end

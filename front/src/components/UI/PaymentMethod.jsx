import React, { useState, useEffect } from "react";
import axios from "axios";
import kaspiQr from "../../assets/all-images/kaspiqr.png"; // Импортируем изображение QR-кода
import "../../styles/payment-method.css";

const PaymentMethod = () => {
  const [cardDetails, setCardDetails] = useState({
    cardNumber: "",
    expiryDate: "",
    cvv: "",
  });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [rentalId, setRentalId] = useState(null); // Храним ID аренды
  const [paymentMethod, setPaymentMethod] = useState(null); // Храним выбранный способ оплаты

  // Получение rental_id для текущего пользователя
  const getUserRentalId = async () => {
    const token = localStorage.getItem("token");

    // Логируем наличие токена
    console.log("Token from localStorage:", token);
    
    if (!token) {
      setMessage("Авторизация необходима.");
      return;
    }

    try {
      const response = await axios.get(
        "http://127.0.0.1:8000/api/rentals/", // Эндпоинт для получения данных об аренде
        {
          headers: {
            Authorization: `Bearer ${token}`, // Передаем токен в заголовке
          },
        }
      );

      console.log("Rental data response:", response.data); // Логируем ответ

      if (response.data && response.data.length > 0) {
        // Проверяем, есть ли аренда
        setRentalId(response.data[0].id); // Устанавливаем rental_id из первого элемента массива
      } else {
        setMessage("Не удалось найти аренду.");
      }
    } catch (error) {
      console.error("Error while fetching rental:", error); // Логируем ошибку
      setMessage("Не удалось получить аренду.");
    }
  };

  useEffect(() => {
    getUserRentalId(); // Получаем rental_id при загрузке компонента
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCardDetails((prev) => ({ ...prev, [name]: value }));
  };

  const handlePayment = async () => {
    const token = localStorage.getItem("token");

    // Логируем состояние перед оплатой
    console.log("Token before payment:", token);
    console.log("Rental ID before payment:", rentalId);

    if (!token || !rentalId) {
      setMessage("Авторизация или аренда необходимы.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/mock-payment/",
        {
          rental_id: rentalId,
          card_number: cardDetails.cardNumber,
          expiry_date: cardDetails.expiryDate,
          cvv: cardDetails.cvv,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`, // Передаем токен в заголовке
          },
        }
      );

      setMessage(response.data.status || "Платеж успешно обработан.");
    } catch (error) {
      setMessage(
        error.response?.data?.error || "Платеж успешно обработан."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="payment-method-selection mt-3">
        <button
          onClick={() => setPaymentMethod("qr")}
          className="btn btn-secondary"
        >
          Оплата через QR
        </button>
        <button
          onClick={() => setPaymentMethod("card")}
          className="btn btn-secondary ml-3"
        >
          Оплата картой
        </button>
      </div>

      <div className="payment mt-3 d-flex align-items-center justify-content-between">
        {paymentMethod === "qr" && (
          <img
            src={kaspiQr}
            alt="Kaspi QR Code"
            style={{
              width: "320px",
              height: "380px",
              position: "relative",
              left: "-1.8cm",
            }}
          />
        )}
      </div>

      {paymentMethod === "card" && (
        <div className="card-payment-form mt-4">
          <h5>Оплата картой</h5>
          <form>
            <div className="form-group">
              <label htmlFor="cardNumber">Номер карты</label>
              <input
                type="text"
                id="cardNumber"
                name="cardNumber"
                value={cardDetails.cardNumber}
                onChange={handleChange}
                className="form-control"
                placeholder="Введите номер карты"
              />
            </div>
            <div className="form-group">
              <label htmlFor="expiryDate">Срок действия</label>
              <input
                type="text"
                id="expiryDate"
                name="expiryDate"
                value={cardDetails.expiryDate}
                onChange={handleChange}
                className="form-control"
                placeholder="MM/YY"
              />
            </div>
            <div className="form-group">
              <label htmlFor="cvv">CVV</label>
              <input
                type="text"
                id="cvv"
                name="cvv"
                value={cardDetails.cvv}
                onChange={handleChange}
                className="form-control"
                placeholder="Введите CVV"
              />
            </div>
            <button
              type="button"
              onClick={handlePayment}
              className="btn btn-primary mt-3"
              disabled={loading}
            >
              {loading ? "Обработка..." : "Оплатить"}
            </button>
          </form>

          {message && <p className="mt-3">{message}</p>}
        </div>
      )}
    </>
  );
};

export default PaymentMethod;

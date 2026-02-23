# Example: Hotel Booking Feature

> Complete walkthrough of the Plan-to-TDD methodology for a hotel booking feature.

## Feature Request

**User Story:** As a traveler, I want to book a hotel room so that I have accommodation for my trip.

---

## Step 1: Feature Decomposition

### User Journey
```
User searches hotels → Views results → Selects room → 
Enters details → Confirms payment → Receives confirmation
```

### System Components (The Boxes)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BOOKING FLOW                                   │
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │  Search  │───▶│  Hotel   │───▶│ Booking  │───▶│ Payment  │             │
│  │  Service │    │  Service │    │  Service │    │  Service │             │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘             │
│       │              │               │               │                     │
│       ▼              ▼               ▼               ▼                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ MongoDB  │    │ MongoDB  │    │ MongoDB  │    │  Stripe  │             │
│  │ (Hotels) │    │ (Rooms)  │    │(Bookings)│    │   API    │             │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Boundaries
- **Search Service:** Query hotels by location, dates, guests
- **Hotel Service:** Get hotel details, room availability, pricing
- **Booking Service:** Create reservations, manage hold periods
- **Payment Service:** Process payments via Stripe, handle refunds

### Data Flows
```
SearchRequest → [Search] → HotelList
HotelId + Dates → [Hotel] → RoomAvailability
RoomSelection + GuestInfo → [Booking] → ReservationHold
ReservationId + PaymentDetails → [Payment] → ConfirmedBooking
```

---

## Step 2: Contract Definitions

### Contract 1: Search → Hotel Service

```typescript
// contracts/search-hotel.contract.ts

interface SearchToHotelContract {
  // Request
  request: {
    hotelIds: string[];
    checkIn: Date;
    checkOut: Date;
    guests: { adults: number; children: number };
  };
  
  // Response
  response: {
    hotels: Array<{
      id: string;
      name: string;
      availableRooms: number;
      lowestPrice: number;
      currency: string;
    }>;
  };
  
  // Error Cases
  errors: {
    INVALID_DATES: 'Check-out must be after check-in';
    NO_AVAILABILITY: 'No rooms available for selected dates';
    HOTEL_NOT_FOUND: 'Hotel does not exist';
  };
}
```

### Contract 2: Booking → Payment Service

```typescript
// contracts/booking-payment.contract.ts

interface BookingToPaymentContract {
  // Request
  request: {
    reservationId: string;
    amount: number;
    currency: string;
    paymentMethod: {
      type: 'card';
      token: string; // Stripe token
    };
    metadata: {
      hotelId: string;
      guestEmail: string;
    };
  };
  
  // Response
  response: {
    success: boolean;
    paymentId: string;
    status: 'completed' | 'pending' | 'failed';
    receiptUrl?: string;
  };
  
  // Error Cases
  errors: {
    CARD_DECLINED: 'Payment card was declined';
    INSUFFICIENT_FUNDS: 'Insufficient funds';
    RESERVATION_EXPIRED: 'Reservation hold has expired';
    STRIPE_ERROR: 'Payment processor unavailable';
  };
}
```

---

## Step 3: Test Structure

### E2E Tests (tests/e2e/booking.spec.ts)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Hotel Booking - User Journey', () => {
  
  test('User can complete a hotel booking successfully', async ({ page }) => {
    // Arrange
    await page.goto('/hotels');
    
    // Act: Search
    await page.fill('[data-testid="location-input"]', 'Tel Aviv');
    await page.fill('[data-testid="checkin-date"]', '2024-03-01');
    await page.fill('[data-testid="checkout-date"]', '2024-03-05');
    await page.click('[data-testid="search-button"]');
    
    // Act: Select hotel and room
    await page.click('[data-testid="hotel-card"]:first-child');
    await page.click('[data-testid="room-select"]:first-child');
    
    // Act: Fill guest details
    await page.fill('[data-testid="guest-name"]', 'John Doe');
    await page.fill('[data-testid="guest-email"]', 'john@example.com');
    
    // Act: Payment (using Stripe test card)
    await page.fill('[data-testid="card-number"]', '4242424242424242');
    await page.fill('[data-testid="card-expiry"]', '12/25');
    await page.fill('[data-testid="card-cvc"]', '123');
    await page.click('[data-testid="confirm-booking"]');
    
    // Assert
    await expect(page.locator('[data-testid="booking-confirmation"]'))
      .toBeVisible();
    await expect(page.locator('[data-testid="booking-reference"]'))
      .toHaveText(/^BK-/);
  });
  
  test('User sees error when payment fails', async ({ page }) => {
    // ... setup to reach payment
    
    // Use Stripe test card that declines
    await page.fill('[data-testid="card-number"]', '4000000000000002');
    await page.click('[data-testid="confirm-booking"]');
    
    // Assert
    await expect(page.locator('[data-testid="payment-error"]'))
      .toContainText('card was declined');
  });
});
```

### Integration Tests (tests/integration/booking-payment.test.ts)

```typescript
import { BookingService } from '@/services/booking';
import { PaymentService } from '@/services/payment';
import { createMockStripe } from '../mocks/stripe';

describe('Booking → Payment Integration', () => {
  let bookingService: BookingService;
  let paymentService: PaymentService;
  let mockStripe: ReturnType<typeof createMockStripe>;
  
  beforeEach(() => {
    mockStripe = createMockStripe();
    paymentService = new PaymentService(mockStripe);
    bookingService = new BookingService({ paymentService });
  });
  
  test('Contract: Successful payment confirms booking', async () => {
    // Arrange
    const reservation = await bookingService.createHold({
      roomId: 'room-123',
      guestEmail: 'test@example.com',
      checkIn: new Date('2024-03-01'),
      checkOut: new Date('2024-03-05'),
    });
    
    mockStripe.paymentIntents.create.mockResolvedValue({
      id: 'pi_123',
      status: 'succeeded',
    });
    
    // Act
    const result = await bookingService.confirmWithPayment({
      reservationId: reservation.id,
      paymentToken: 'tok_visa',
    });
    
    // Assert: Contract fulfilled
    expect(result.status).toBe('confirmed');
    expect(result.paymentId).toBe('pi_123');
    expect(mockStripe.paymentIntents.create).toHaveBeenCalledWith(
      expect.objectContaining({
        amount: reservation.totalAmount,
        currency: 'usd',
      })
    );
  });
  
  test('Contract: Handles Stripe timeout gracefully', async () => {
    // Arrange
    const reservation = await bookingService.createHold({
      roomId: 'room-123',
      guestEmail: 'test@example.com',
      checkIn: new Date('2024-03-01'),
      checkOut: new Date('2024-03-05'),
    });
    
    mockStripe.paymentIntents.create.mockRejectedValue(
      new Error('Request timeout')
    );
    
    // Act & Assert
    await expect(
      bookingService.confirmWithPayment({
        reservationId: reservation.id,
        paymentToken: 'tok_visa',
      })
    ).rejects.toThrow('STRIPE_ERROR');
    
    // Reservation should remain in hold status
    const updated = await bookingService.getReservation(reservation.id);
    expect(updated.status).toBe('hold');
  });
  
  test('Contract: Releases hold when payment fails', async () => {
    // Arrange
    const reservation = await bookingService.createHold({
      roomId: 'room-123',
      guestEmail: 'test@example.com',
      checkIn: new Date('2024-03-01'),
      checkOut: new Date('2024-03-05'),
    });
    
    mockStripe.paymentIntents.create.mockResolvedValue({
      id: 'pi_123',
      status: 'requires_payment_method',
      last_payment_error: { code: 'card_declined' },
    });
    
    // Act
    const result = await bookingService.confirmWithPayment({
      reservationId: reservation.id,
      paymentToken: 'tok_visa',
    });
    
    // Assert
    expect(result.status).toBe('failed');
    expect(result.error).toBe('CARD_DECLINED');
  });
});
```

### Unit Tests (tests/unit/booking-service.test.ts)

```typescript
import { BookingService } from '@/services/booking';
import { 
  InvalidDatesError, 
  RoomUnavailableError 
} from '@/errors/booking';

describe('BookingService Unit Tests', () => {
  
  describe('createHold()', () => {
    let service: BookingService;
    let mockRoomRepo: jest.Mocked<RoomRepository>;
    let mockBookingRepo: jest.Mocked<BookingRepository>;
    
    beforeEach(() => {
      mockRoomRepo = createMockRoomRepo();
      mockBookingRepo = createMockBookingRepo();
      service = new BookingService({
        roomRepo: mockRoomRepo,
        bookingRepo: mockBookingRepo,
      });
    });
    
    test('creates hold for available room', async () => {
      // Arrange
      mockRoomRepo.isAvailable.mockResolvedValue(true);
      mockRoomRepo.getPrice.mockResolvedValue(100);
      mockBookingRepo.create.mockResolvedValue({ id: 'res-123' });
      
      // Act
      const result = await service.createHold({
        roomId: 'room-123',
        guestEmail: 'test@example.com',
        checkIn: new Date('2024-03-01'),
        checkOut: new Date('2024-03-05'),
      });
      
      // Assert
      expect(result.id).toBe('res-123');
      expect(result.status).toBe('hold');
      expect(result.totalAmount).toBe(400); // 4 nights × $100
    });
    
    test('throws InvalidDatesError when checkout before checkin', async () => {
      // Act & Assert
      await expect(
        service.createHold({
          roomId: 'room-123',
          guestEmail: 'test@example.com',
          checkIn: new Date('2024-03-05'),
          checkOut: new Date('2024-03-01'), // Before check-in!
        })
      ).rejects.toThrow(InvalidDatesError);
    });
    
    test('throws RoomUnavailableError when room not available', async () => {
      // Arrange
      mockRoomRepo.isAvailable.mockResolvedValue(false);
      
      // Act & Assert
      await expect(
        service.createHold({
          roomId: 'room-123',
          guestEmail: 'test@example.com',
          checkIn: new Date('2024-03-01'),
          checkOut: new Date('2024-03-05'),
        })
      ).rejects.toThrow(RoomUnavailableError);
    });
  });
  
  describe('calculateNights()', () => {
    test('returns correct nights for same month dates', () => {
      const nights = BookingService.calculateNights(
        new Date('2024-03-01'),
        new Date('2024-03-05')
      );
      expect(nights).toBe(4);
    });
    
    test('returns correct nights across month boundary', () => {
      const nights = BookingService.calculateNights(
        new Date('2024-02-28'),
        new Date('2024-03-02')
      );
      expect(nights).toBe(3);
    });
    
    test('returns 0 for same day', () => {
      const nights = BookingService.calculateNights(
        new Date('2024-03-01'),
        new Date('2024-03-01')
      );
      expect(nights).toBe(0);
    });
  });
});
```

---

## Step 4: Implementation Order (Build Plan)

### Task Breakdown

```markdown
## Phase 1: Scaffold (Day 1)
- [ ] Create directory structure
- [ ] Define TypeScript interfaces from contracts
- [ ] Create empty service classes
- [ ] Set up test configuration

## Phase 2: E2E Red (Day 1)
- [ ] Write E2E test for happy path booking
- [ ] Write E2E test for payment failure
- [ ] Verify tests fail (no implementation yet)

## Phase 3: Integration Red (Day 2)
- [ ] Write Booking → Payment integration tests
- [ ] Write Search → Hotel integration tests
- [ ] Create mock factories for external services
- [ ] Verify tests fail

## Phase 4: TDD Units (Days 3-5)

### BookingService Units
- [ ] RED: test createHold for available room
- [ ] GREEN: implement createHold
- [ ] RED: test InvalidDatesError
- [ ] GREEN: implement date validation
- [ ] RED: test RoomUnavailableError
- [ ] GREEN: implement availability check
- [ ] REFACTOR: extract calculateNights utility

### PaymentService Units
- [ ] RED: test processPayment success
- [ ] GREEN: implement Stripe integration
- [ ] RED: test card declined handling
- [ ] GREEN: implement error mapping
- [ ] RED: test timeout handling
- [ ] GREEN: implement retry logic
- [ ] REFACTOR: extract error types

### SearchService Units
- [ ] RED: test search by location
- [ ] GREEN: implement MongoDB query
- [ ] RED: test date filtering
- [ ] GREEN: implement availability filter
- [ ] REFACTOR: optimize query performance

## Phase 5: Integration Green (Day 6)
- [ ] Run integration tests
- [ ] Fix any contract mismatches
- [ ] Verify all integration tests pass

## Phase 6: E2E Green (Day 6)
- [ ] Run E2E tests
- [ ] Fix any UI/flow issues
- [ ] Verify complete journey works

## Phase 7: Refactor (Day 7)
- [ ] Code review and cleanup
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] ADR for key decisions
```

---

## Feedback Loop Example

### Pain Detected During TDD

**Symptom:** While writing unit tests for `BookingService`, setup required:
- Mocking MongoDB connection
- Mocking room repository
- Mocking booking repository
- Mocking email service
- Mocking inventory service
- 60+ lines just to create the test fixture

**Diagnosis:** `BookingService` has too many direct dependencies.

**Return to Design:**

Before:
```
┌─────────────────────────────────────────────┐
│             BookingService                  │
│  - MongoDB                                  │
│  - RoomRepository                           │
│  - BookingRepository                        │
│  - EmailService                             │
│  - InventoryService                         │
│  - PaymentService                           │
└─────────────────────────────────────────────┘
```

After refactor:
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Booking    │────▶│ Notification │────▶│    Email     │
│   Service    │     │   Service    │     │   Service    │
└──────────────┘     └──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐
│  Repository  │ (abstracts MongoDB + Rooms + Bookings)
│   Layer      │
└──────────────┘
```

**Result:** Tests now need only 2 mocks instead of 6.